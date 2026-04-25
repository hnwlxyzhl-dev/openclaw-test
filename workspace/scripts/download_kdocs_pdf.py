#!/usr/bin/env python3.11
"""
Download a KDocs PDF by scrolling through each page,
capturing page screenshots, and assembling into a PDF using Pillow.
"""
import asyncio
import sys
import os
from PIL import Image
import io

async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.kdocs.cn/l/cjLklIF0rSPO"
    output = sys.argv[2] if len(sys.argv) > 2 else "/home/admin/.openclaw/workspace/国金证券-机器人行业2026年度策略.pdf"
    
    print(f"URL: {url}")
    print(f"Output: {output}")
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={"width": 1000, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Loading page...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Wait for PDF viewer to load
        print("Waiting for PDF viewer...")
        await page.wait_for_selector('.pdf-page', timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Find total pages
        total_pages = await page.evaluate("""() => {
            const pages = document.querySelectorAll('.pdf-page');
            return pages.length;
        }""")
        print(f"Total pages: {total_pages}")
        
        if total_pages == 0:
            print("ERROR: No PDF pages found!")
            await browser.close()
            return
        
        # Get page dimensions
        page_dims = await page.evaluate("""() => {
            const first = document.querySelector('.pdf-page');
            if (!first) return null;
            const rect = first.getBoundingClientRect();
            return {
                width: rect.width,
                height: rect.height
            };
        }""")
        print(f"Page dimensions: {page_dims['width']}x{page_dims['height']}")
        
        # Pre-scroll to load all pages
        print("Pre-loading all pages by scrolling...")
        scroll_container = await page.evaluate("""() => {
            const container = document.querySelector('.pdf-pages-container') 
                           || document.querySelector('.pdf-page-wrapper')
                           || document.querySelector('[class*="scroll"]');
            if (container) {
                return {
                    scrollHeight: container.scrollHeight,
                    found: true
                };
            }
            // Try the page wrapper
            const wrapper = document.querySelector('.pdf-page-wrapper');
            if (wrapper) {
                return { scrollHeight: wrapper.scrollHeight, found: true };
            }
            return { found: false };
        }""")
        
        if scroll_container.get('found'):
            total_height = scroll_container['scrollHeight']
            print(f"  Total scroll height: {total_height}px")
            
            # Scroll in increments
            step = 1000
            pos = 0
            while pos < total_height:
                js_step = "(pos) => { const c = document.querySelector('.pdf-pages-container') || document.querySelector('.pdf-page-wrapper'); if(c) c.scrollTop = pos; }"
                await page.evaluate(js_step, pos)
                await page.wait_for_timeout(200)
                pos += step
        
        # Scroll back to top
        await page.evaluate("""() => {
            const container = document.querySelector('.pdf-pages-container') 
                           || document.querySelector('.pdf-page-wrapper');
            if (container) container.scrollTop = 0;
        }""")
        await page.wait_for_timeout(2000)
        
        # Capture each page using canvas content
        print("Capturing pages...")
        pdf_images = []
        
        page_h = page_dims['height']
        page_w = page_dims['width']
        
        for i in range(total_pages):
            print(f"  Page {i+1}/{total_pages}...", end=" ", flush=True)
            
            # Scroll to this page
            scroll_pos = i * (page_h + 16)  # 16px gap between pages
            js_scroll = """
            (pos) => {
                const container = document.querySelector('.pdf-pages-container') 
                               || document.querySelector('.pdf-page-wrapper');
                if (container) container.scrollTop = pos;
            }
            """
            await page.evaluate(js_scroll, scroll_pos)
            await page.wait_for_timeout(800)
            
            # Capture this page's canvases
            js_code = """
            (pageIndex) => {
                const pages = document.querySelectorAll('.pdf-page');
                const targetPage = pages[pageIndex];
                if (!targetPage) return null;
                
                const canvases = targetPage.querySelectorAll('canvas');
                const results = [];
                for (const canvas of canvases) {
                    if (canvas.width > 10 && canvas.height > 10) {
                        try {
                            results.push({
                                data: canvas.toDataURL('image/png'),
                                x: canvas.offsetLeft,
                                y: canvas.offsetTop,
                                w: canvas.width,
                                h: canvas.height
                            });
                        } catch(e) {}
                    }
                }
                return results;
            }
            """
            tiles_data = await page.evaluate(js_code, i)
            
            if not tiles_data:
                print("NO CANVAS, using screenshot fallback")
                # Fallback: take a screenshot of the page element
                try:
                    page_el = page.locator('.pdf-page').nth(i)
                    shot = await page_el.screenshot(type='png')
                    img = Image.open(io.BytesIO(shot))
                    pdf_images.append(img)
                    print(f"OK ({img.size[0]}x{img.size[1]})")
                except Exception as e:
                    print(f"FAILED: {e}")
                continue
            
            # Composite the tiles into one image
            max_x = max(d['x'] + d['w'] for d in tiles_data)
            max_y = max(d['y'] + d['h'] for d in tiles_data)
            
            # Use 2x resolution for quality
            scale = 2.0
            img_w = int(page_w * scale)
            img_h = int(page_h * scale)
            
            composite = Image.new('RGB', (img_w, img_h), (255, 255, 255))
            
            tile_scale = img_w / max(max_x, 1)
            
            for tile in tiles_data:
                data_url = tile['data']
                if not data_url.startswith('data:image'):
                    continue
                b64 = data_url.split(',')[1]
                img_data = __import__('base64').b64decode(b64)
                tile_img = Image.open(io.BytesIO(img_data))
                
                tx = int(tile['x'] * tile_scale)
                ty = int(tile['y'] * tile_scale)
                tw = int(tile['w'] * tile_scale)
                th = int(tile['h'] * tile_scale)
                
                tile_img = tile_img.resize((tw, th), Image.LANCZOS)
                composite.paste(tile_img, (tx, ty))
            
            pdf_images.append(composite)
            print(f"OK ({composite.size[0]}x{composite.size[1]})")
        
        # Save as PDF
        print(f"\nSaving PDF ({len(pdf_images)} pages)...")
        if pdf_images:
            first = pdf_images[0]
            pdf_images[0].save(
                output,
                format='PDF',
                save_all=True,
                append_images=pdf_images[1:],
                resolution=150,
                quality=90
            )
            file_size = os.path.getsize(output)
            print(f"Done! Saved: {output}")
            print(f"Size: {file_size / 1024 / 1024:.1f} MB")
        else:
            print("ERROR: No pages captured!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
