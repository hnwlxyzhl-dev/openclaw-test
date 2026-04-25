#!/usr/bin/env python3.11
"""
Capture all 58 pages of a KDocs PDF via CDP, then combine into a single PDF.
Connects to the openclaw browser's CDP websocket.
"""
import asyncio
import json
import os
import sys
import base64
import websockets

OUTPUT_DIR = "/home/admin/.openclaw/workspace/kdocs_pages"
OUTPUT_PDF = "/home/admin/.openclaw/workspace/国金证券-机器人行业2026年度策略.pdf"
TOTAL_PAGES = 58

# The openclaw browser CDP wsUrl from the browser tool
CDP_URL = None  # Will be extracted from the browser status

async def cdp_send(ws, method, params=None, timeout=30):
    """Send a CDP command and return the result."""
    msg_id = getattr(cdp_send, 'next_id', 1)
    cdp_send.next_id = msg_id + 1
    
    cmd = {"id": msg_id, "method": method}
    if params:
        cmd["params"] = params
    
    await ws.send(json.dumps(cmd))
    
    # Read responses until we get ours
    while True:
        resp = await asyncio.wait_for(ws.recv(), timeout=timeout)
        data = json.loads(resp)
        if data.get("id") == msg_id:
            if "error" in data:
                raise Exception(f"CDP error: {data['error']}")
            return data.get("result", {})
        # Ignore events

async def capture_pages(ws_url):
    """Connect to browser and capture all pages."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        print(f"Connected to CDP: {ws_url[:60]}...")
        
        # Enable necessary domains
        await cdp_send(ws, "Page.enable")
        await cdp_send(ws, "Runtime.enable")
        
        # Get current scroll info
        scroll_info = await cdp_send(ws, "Runtime.evaluate", {
            "expression": """
            (() => {
                const parent = document.querySelector('.pdf-page-wrapper')?.parentElement;
                if (!parent) return { error: 'no container' };
                return { 
                    scrollTop: parent.scrollTop, 
                    scrollHeight: parent.scrollHeight, 
                    clientHeight: parent.clientHeight 
                };
            })()
            """
        })
        print(f"Scroll info: {scroll_info.get('result', {}).get('value', scroll_info)}")
        
        page_h = scroll_info.get('result', {}).get('value', {}).get('scrollHeight', 44000) / TOTAL_PAGES
        print(f"Estimated page height: {page_h:.0f}px")
        
        captured = 0
        for i in range(TOTAL_PAGES):
            page_num = i + 1
            scroll_pos = i * (page_h + 8)  # small gap
            
            # Scroll to page
            result = await cdp_send(ws, "Runtime.evaluate", {
                "expression": f"""
                (() => {{
                    const parent = document.querySelector('.pdf-page-wrapper')?.parentElement;
                    if (parent) {{
                        parent.scrollTop = {scroll_pos};
                        return true;
                    }}
                    return false;
                }})()
                """
            })
            
            # Wait for render
            await asyncio.sleep(0.8)
            
            # Update page number display to ensure correct page
            await cdp_send(ws, "Runtime.evaluate", {
                "expression": f"""
                (() => {{
                    const input = document.querySelector('.kd-input-inner[placeholder=""]');
                    const allInputs = document.querySelectorAll('.kd-input-inner');
                    for (const inp of allInputs) {{
                        if (inp.value.includes('/58') || inp.value.includes('/')) {{
                            inp.focus();
                            inp.value = '{page_num}/58';
                            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                            inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                            inp.blur();
                        }}
                    }}
                }})()
                """
            })
            await asyncio.sleep(1.0)
            
            # Find the visible pdf-page element and get its position
            page_pos = await cdp_send(ws, "Runtime.evaluate", {
                "expression": """
                (() => {
                    const pages = document.querySelectorAll('.pdf-page');
                    const visible = [];
                    const parent = document.querySelector('.pdf-page-wrapper')?.parentElement;
                    const scrollTop = parent ? parent.scrollTop : 0;
                    const viewH = parent ? parent.clientHeight : 800;
                    
                    for (let i = 0; i < pages.length; i++) {
                        const r = pages[i].getBoundingClientRect();
                        if (r.top < viewH + 100 && r.bottom > -100) {
                            visible.push({
                                idx: i,
                                top: r.top,
                                bottom: r.bottom,
                                width: r.width,
                                height: r.height,
                                loaded: pages[i].classList.contains('loaded')
                            });
                        }
                    }
                    return { scrollTop, viewH, visible, totalPages: pages.length };
                })()
                """
            })
            
            vis_info = page_pos.get('result', {}).get('value', {})
            visible_pages = vis_info.get('visible', [])
            
            if not visible_pages:
                print(f"  Page {page_num}: no visible page found, skipping")
                continue
            
            # Use the first visible page
            vp = visible_pages[0]
            print(f"  Page {page_num}: visible DOM idx={vp['idx']}, loaded={vp['loaded']}, pos={vp['top']:.0f}-{vp['bottom']:.0f}", end="")
            
            if not vp['loaded']:
                print(" (not loaded, waiting...)", end="")
                await asyncio.sleep(1.5)
            
            # Capture this page's canvas content
            canvas_data = await cdp_send(ws, "Runtime.evaluate", {
                "expression": f"""
                (() => {{
                    const pages = document.querySelectorAll('.pdf-page');
                    const target = pages[{vp['idx']}];
                    if (!target) return {{ error: 'not found' }};
                    
                    const canvases = target.querySelectorAll('canvas');
                    const results = [];
                    for (const c of canvases) {{
                        if (c.width > 10 && c.height > 10) {{
                            try {{
                                results.push({{
                                    data: c.toDataURL('image/png'),
                                    x: c.offsetLeft,
                                    y: c.offsetTop,
                                    w: c.width,
                                    h: c.height
                                }});
                            }} catch(e) {{}}
                        }}
                    }}
                    return {{ canvasCount: results.length, pageW: target.offsetWidth, pageH: target.offsetHeight }};
                }})()
                """
            })
            
            cv_info = canvas_data.get('result', {}).get('value', {})
            canvas_count = cv_info.get('canvasCount', 0)
            print(f", canvases={canvas_count}", end="")
            
            if canvas_count == 0:
                print(" -> NO CANVAS")
                continue
            
            # Now get the actual data (separate call to avoid size limits in evaluate)
            # Get each canvas data URL separately
            all_tiles = []
            for ci in range(canvas_count):
                tile_data = await cdp_send(ws, "Runtime.evaluate", {
                    "expression": f"""
                    (() => {{
                        const pages = document.querySelectorAll('.pdf-page');
                        const target = pages[{vp['idx']}];
                        const canvases = target.querySelectorAll('canvas');
                        const c = canvases[{ci}];
                        if (!c || c.width < 10) return null;
                        return {{
                            data: c.toDataURL('image/png'),
                            x: c.offsetLeft,
                            y: c.offsetTop,
                            w: c.width,
                            h: c.height
                        }};
                    }})()
                    """
                })
                td = tile_data.get('result', {}).get('value')
                if td and td.get('data'):
                    all_tiles.append(td)
            
            if not all_tiles:
                print(" -> FAILED to get tile data")
                continue
            
            # Save tile data as JSON for later processing
            tile_file = os.path.join(OUTPUT_DIR, f"page_{page_num:03d}.json")
            with open(tile_file, 'w') as f:
                json.dump({
                    "page": page_num,
                    "pageW": cv_info.get('pageW', 760),
                    "pageH": cv_info.get('pageH', 1075),
                    "tiles": all_tiles
                }, f)
            
            captured += 1
            print(f" -> OK")
        
        print(f"\nCaptured {captured}/{TOTAL_PAGES} pages")
        
        # Scroll back to top
        await cdp_send(ws, "Runtime.evaluate", {
            "expression": "document.querySelector('.pdf-page-wrapper')?.parentElement?.scrollTo(0, 0)"
        })

def combine_to_pdf():
    """Combine captured page JSON files into a single PDF."""
    from PIL import Image
    import io
    
    print("Combining pages into PDF...")
    
    pages = sorted(Path(OUTPUT_DIR).glob("page_*.json"))
    if not pages:
        print("ERROR: No page files found!")
        return False
    
    pdf_images = []
    for pf in pages:
        with open(pf) as f:
            data = json.load(f)
        
        page_w = data['pageW']
        page_h = data['pageH']
        tiles = data['tiles']
        
        if not tiles:
            continue
        
        # Find bounding box of all tiles
        max_x = max(t['x'] + t['w'] for t in tiles)
        max_y = max(t['y'] + t['h'] for t in tiles)
        
        scale = page_w / max(max_x, 1)
        img_w = int(page_w * 2)
        img_h = int(page_h * 2)
        
        composite = Image.new('RGB', (img_w, img_h), (255, 255, 255))
        
        for tile in tiles:
            data_url = tile['data']
            if not data_url.startswith('data:image'):
                continue
            b64 = data_url.split(',')[1]
            img_bytes = base64.b64decode(b64)
            tile_img = Image.open(io.BytesIO(img_bytes))
            
            tx = int(tile['x'] * scale * 2)
            ty = int(tile['y'] * scale * 2)
            tw = int(tile['w'] * scale * 2)
            th = int(tile['h'] * scale * 2)
            
            tile_img = tile_img.resize((tw, th), Image.LANCZOS)
            composite.paste(tile_img, (tx, ty))
        
        pdf_images.append(composite)
    
    if pdf_images:
        pdf_images[0].save(
            OUTPUT_PDF,
            format='PDF',
            save_all=True,
            append_images=pdf_images[1:],
            resolution=150
        )
        file_size = os.path.getsize(OUTPUT_PDF)
        print(f"PDF saved: {OUTPUT_PDF}")
        print(f"Size: {file_size / 1024 / 1024:.1f} MB, Pages: {len(pdf_images)}")
        return True
    else:
        print("ERROR: No images to combine!")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3.11 kdocs_capture.py <cdp_ws_url>")
        print("       python3.11 kdocs_capture.py combine")
        sys.exit(1)
    
    if sys.argv[1] == "combine":
        combine_to_pdf()
        return
    
    ws_url = sys.argv[1]
    await capture_pages(ws_url)
    
    # Auto-combine
    combine_to_pdf()

if __name__ == "__main__":
    asyncio.run(main())
