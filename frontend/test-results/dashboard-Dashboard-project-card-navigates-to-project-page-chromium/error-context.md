# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard >> project card navigates to project page
- Location: e2e/dashboard.spec.ts:26:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[class*=\'rounded-xl\']').filter({ hasText: /《/ }).first()
    - locator resolved to <div tabindex="0" class="group relative cursor-pointer overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-md transition-colors hover:border-amber-600/30 hover:shadow-lg">…</div>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">…</div> intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">…</div> intercepts pointer events
    - retrying click action
      - waiting 100ms
    54 × waiting for element to be visible, enabled and stable
       - element is visible, enabled and stable
       - scrolling into view if needed
       - done scrolling
       - <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">…</div> intercepts pointer events
     - retrying click action
       - waiting 500ms

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e5]:
    - img [ref=e8]
    - navigation [ref=e13]:
      - link "项目" [ref=e14] [cursor=pointer]:
        - /url: /
        - img [ref=e15]
    - generic [ref=e18]: v0.1
  - main [ref=e20]:
    - generic [ref=e22]:
      - generic [ref=e23]:
        - generic [ref=e24]:
          - heading "ScriptForge" [level=1] [ref=e25]
          - paragraph [ref=e26]: AI 辅助剧本创作工坊 — 将小说转换为结构化剧本
        - button "新建项目" [ref=e27]:
          - img [ref=e28]
          - text: 新建项目
      - heading "📖 我的项目" [level=2] [ref=e29]
      - generic [ref=e31] [cursor=pointer]:
        - generic [ref=e33]:
          - img [ref=e35]
          - generic [ref=e37]:
            - heading "《三体改编》" [level=3] [ref=e38]
            - paragraph [ref=e39]: 6月5日 12:29
          - button "删除项目" [ref=e40]:
            - img [ref=e41]
        - paragraph [ref=e44]: 刘慈欣科幻巨著改编
        - generic [ref=e48]: 3 章
        - generic [ref=e49]:
          - generic [ref=e50]: 🎬 电影
          - generic [ref=e51]: 草稿
      - generic [ref=e53]:
        - button "跳过引导" [ref=e54]:
          - img [ref=e55]
        - generic [ref=e65]:
          - img [ref=e67]
          - heading "欢迎使用 ScriptForge" [level=2] [ref=e69]
          - paragraph [ref=e70]: ScriptForge 是一款 AI 驱动的小说转剧本工具。只需 5 步，即可将您的小说转换为专业剧本格式。
          - button "下一步" [ref=e72]:
            - text: 下一步
            - img [ref=e73]
          - button "跳过引导" [ref=e75]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("Dashboard", () => {
  4  |   test("page loads with title", async ({ page }) => {
  5  |     await page.goto("/");
  6  |     await expect(page.locator("text=ScriptForge")).toBeVisible();
  7  |   });
  8  | 
  9  |   test("can create a project", async ({ page }) => {
  10 |     await page.goto("/");
  11 | 
  12 |     // Open create modal
  13 |     await page.click("text=新建项目");
  14 | 
  15 |     // Fill form
  16 |     await page.fill('input[placeholder="项目名称"]', "E2E 测试项目");
  17 |     await page.fill('textarea', "这是一个 E2E 测试项目");
  18 | 
  19 |     // Submit
  20 |     await page.click("text=创建");
  21 | 
  22 |     // Should see the project card
  23 |     await expect(page.locator("text=E2E 测试项目")).toBeVisible();
  24 |   });
  25 | 
  26 |   test("project card navigates to project page", async ({ page }) => {
  27 |     await page.goto("/");
  28 | 
  29 |     // Wait for projects to load
  30 |     await page.waitForSelector("text=我的项目");
  31 | 
  32 |     // Click first project card if any
  33 |     const cards = page.locator("[class*='rounded-xl']").filter({ hasText: /《/ });
  34 |     const count = await cards.count();
  35 | 
  36 |     if (count > 0) {
> 37 |       await cards.first().click();
     |                           ^ Error: locator.click: Test timeout of 30000ms exceeded.
  38 |       // Should navigate to project page
  39 |       await expect(page).toHaveURL(/\/projects\/[\w-]+/);
  40 |     }
  41 |   });
  42 | });
  43 | 
```