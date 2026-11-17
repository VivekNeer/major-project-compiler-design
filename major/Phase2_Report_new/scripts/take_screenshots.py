import time
from playwright.sync_api import sync_playwright
OUT="/home/manas/Desktop/major/Phase2_Report/figures/"
def load(pg, name):
    sel=pg.locator("select").first
    opts=sel.locator("option").all_text_contents()
    vals=sel.locator("option").evaluate_all("els=>els.map(e=>e.value)")
    for v,t in zip(vals,opts):
        if v==name or t.strip().startswith(name):
            sel.select_option(v); time.sleep(0.8); return True
    print("not found",name,vals[:5]); return False
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={"width":1440,"height":900}, device_scale_factor=2)
    pg.goto("http://localhost:8080/", wait_until="networkidle"); time.sleep(1.2)
    # Playground with factorial, AST tab
    load(pg,"factorial"); pg.locator("button.btn.primary").first.click(); time.sleep(1.2)
    pg.screenshot(path=OUT+"gui_playground.png")
    try:
        pg.click("text=AST"); time.sleep(0.6); pg.screenshot(path=OUT+"gui_playground_ast.png")
        pg.click("text=TOKENS"); time.sleep(0.6); pg.screenshot(path=OUT+"gui_playground_tokens.png")
    except Exception as e: print("tab",e)
    # semantic error example
    pg.click("text=IR"); time.sleep(0.3)
    pg.locator(".cm-content").first.click(); pg.keyboard.press("Control+End"); pg.keyboard.type("\nint bad() { return undefined_var + 1; }\n")
    pg.locator("button.btn.primary").first.click(); time.sleep(1.2)
    pg.screenshot(path=OUT+"gui_playground_error.png")
    pg.reload(wait_until="networkidle"); time.sleep(1.0)
    # OptLab with factorial
    pg.click("text=Optimization Lab"); time.sleep(0.6); load(pg,"factorial")
    pg.locator("button.btn.primary").first.click(); time.sleep(2.5); pg.screenshot(path=OUT+"gui_optlab.png")
    # click the DCE stage chip to show diff
    try:
        pg.locator("text=DCE").nth(1).click(); time.sleep(0.6); pg.screenshot(path=OUT+"gui_optlab_diff.png")
    except Exception as e: print("dce",e)
    # Assembly with factorial
    pg.click("text=Assembly"); time.sleep(0.6); load(pg,"factorial")
    pg.locator("button.btn.primary").first.click(); time.sleep(2.0); pg.screenshot(path=OUT+"gui_assembly.png")
    # Explorer with gemm
    pg.click("text=Phase Explorer"); time.sleep(0.6); load(pg,"gemm")
    pg.locator("button.btn.primary").first.click(); time.sleep(15); pg.screenshot(path=OUT+"gui_explorer.png")
    b.close(); print("ok")
