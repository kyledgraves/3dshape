import pytest
from playwright.sync_api import Page, expect
import re
import time

VIEWER_URL = "http://localhost:8082"

def test_viewer_alt_text_visibility(page: Page):
    page.goto(VIEWER_URL)
    placeholder_text = page.locator("#placeholder h1")
    placeholder_text.wait_for(state="attached")
    color = placeholder_text.evaluate("el => window.getComputedStyle(el).color")
    assert color == "rgb(255, 255, 255)", f"Expected white text, but got {color}"

def test_viewer_stream_updates(page: Page):
    page.goto(VIEWER_URL)
    
    connect_btn = page.locator("#btn-connect")
    stream_img = page.locator("#stream")
    placeholder = page.locator("#placeholder")
    
    expect(placeholder).to_be_visible()
    expect(stream_img).to_be_hidden()
    
    connect_btn.click()
    
    expect(stream_img).to_be_visible(timeout=5000)
    expect(placeholder).to_be_hidden()
    expect(stream_img).to_have_attribute("src", re.compile(r"^data:image/jpeg;base64,"), timeout=5000)
    
    page.wait_for_timeout(3000)
    
    frame1_src = stream_img.get_attribute("src")
    
    page.locator("#btn-left").scroll_into_view_if_needed()
    page.locator("#btn-left").click()
    page.wait_for_timeout(3000)
    
    frame2_src = stream_img.get_attribute("src")
    assert frame1_src != frame2_src, "Frame did not update after clicking 'Left'!"
    
    stream_img.click()
    page.mouse.wheel(0, 1000)
    page.wait_for_timeout(1000)
    frame3_src = stream_img.get_attribute("src")
    
    assert frame2_src != frame3_src, "Frame did not update after Mouse Zoom!"
    
    page.screenshot(path="viewer_test_screenshot.png")
    
    # Give UI focus to the image and scroll the mouse wheel
    stream_img.click()
    page.mouse.wheel(0, 1000)
    page.wait_for_timeout(1000)
    frame3_src = stream_img.get_attribute("src")
    
    assert frame2_src != frame3_src, "Frame did not update after Mouse Zoom!"
    
    page.screenshot(path="viewer_test_screenshot.png")
