# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.ts >> Dashboard >> page loads with title
- Location: e2e/dashboard.spec.ts:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=ScriptForge')
Expected: visible
Error: strict mode violation: locator('text=ScriptForge') resolved to 4 elements:
    1) <span class="text-sm font-medium text-neutral-200">ScriptForge</span> aka locator('header').getByText('ScriptForge')
    2) <h1 class="font-display text-2xl font-semibold text-text-primary">ScriptForge</h1> aka getByRole('heading', { name: 'ScriptForge', exact: true })
    3) <h2 class="mb-2 text-xl font-bold text-neutral-100">欢迎使用 ScriptForge</h2> aka getByRole('heading', { name: '欢迎使用 ScriptForge' })
    4) <p class="mb-6 text-sm leading-relaxed text-neutral-400">ScriptForge 是一款 AI 驱动的小说转剧本工具。只需 5 步，即可将您的小说转换为专业…</p> aka getByText('ScriptForge 是一款 AI')

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=ScriptForge')

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
> 6  |     await expect(page.locator("text=ScriptForge")).toBeVisible();
     |                                                    ^ Error: expect(locator).toBeVisible() failed
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
  37 |       await cards.first().click();
  38 |       // Should navigate to project page
  39 |       await expect(page).toHaveURL(/\/projects\/[\w-]+/);
  40 |     }
  41 |   });
  42 | });
  43 | 
```