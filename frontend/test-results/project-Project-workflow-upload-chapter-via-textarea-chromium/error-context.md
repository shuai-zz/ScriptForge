# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: project.spec.ts >> Project workflow >> upload chapter via textarea
- Location: e2e/project.spec.ts:4:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('text=新建项目')
    - locator resolved to <button class="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover">…</button>
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
    55 × waiting for element to be visible, enabled and stable
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
  3  | test.describe("Project workflow", () => {
  4  |   test("upload chapter via textarea", async ({ page }) => {
  5  |     await page.goto("/");
  6  | 
  7  |     // Create a project first
> 8  |     await page.click("text=新建项目");
     |                ^ Error: page.click: Test timeout of 30000ms exceeded.
  9  |     await page.fill('input[placeholder="项目名称"]', "章节测试项目");
  10 |     await page.click("text=创建");
  11 | 
  12 |     // Navigate to project
  13 |     await expect(page.locator("text=章节测试项目")).toBeVisible();
  14 |     await page.click("text=章节测试项目");
  15 | 
  16 |     // Should be on chapters page
  17 |     await expect(page).toHaveURL(/\/projects\/[\w-]+/);
  18 |     await expect(page.locator("text=章节管理")).toBeVisible();
  19 | 
  20 |     // Add chapter via textarea
  21 |     await page.click("text=粘贴文本");
  22 |     await page.fill("textarea", "这是第一章的内容。主角登场。");
  23 |     await page.fill('input[placeholder="章节标题"]', "第一章");
  24 |     await page.click("text=保存");
  25 | 
  26 |     // Chapter should appear
  27 |     await expect(page.locator("text=第一章")).toBeVisible();
  28 |   });
  29 | 
  30 |   test("navigate to script editor", async ({ page }) => {
  31 |     await page.goto("/");
  32 | 
  33 |     // Wait and click first project
  34 |     await page.waitForSelector("text=我的项目");
  35 |     const cards = page.locator("[class*='rounded-xl']").filter({ hasText: /《/ });
  36 |     const count = await cards.count();
  37 | 
  38 |     if (count === 0) {
  39 |       test.skip("No projects available");
  40 |       return;
  41 |     }
  42 | 
  43 |     await cards.first().click();
  44 | 
  45 |     // Navigate to script editor via sidebar
  46 |     await page.click("text=剧本");
  47 |     await expect(page).toHaveURL(/\/projects\/[\w-]+\/script/);
  48 |   });
  49 | });
  50 | 
```