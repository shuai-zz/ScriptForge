import { test, expect } from "@playwright/test";

test.describe("Project workflow", () => {
  test("upload chapter via textarea", async ({ page }) => {
    await page.goto("/");

    // Create a project first
    await page.click("text=新建项目");
    await page.fill('input[placeholder="项目名称"]', "章节测试项目");
    await page.click("text=创建");

    // Navigate to project
    await expect(page.locator("text=章节测试项目")).toBeVisible();
    await page.click("text=章节测试项目");

    // Should be on chapters page
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);
    await expect(page.locator("text=章节管理")).toBeVisible();

    // Add chapter via textarea
    await page.click("text=粘贴文本");
    await page.fill("textarea", "这是第一章的内容。主角登场。");
    await page.fill('input[placeholder="章节标题"]', "第一章");
    await page.click("text=保存");

    // Chapter should appear
    await expect(page.locator("text=第一章")).toBeVisible();
  });

  test("navigate to script editor", async ({ page }) => {
    await page.goto("/");

    // Wait and click first project
    await page.waitForSelector("text=我的项目");
    const cards = page.locator("[class*='rounded-xl']").filter({ hasText: /《/ });
    const count = await cards.count();

    if (count === 0) {
      test.skip("No projects available");
      return;
    }

    await cards.first().click();

    // Navigate to script editor via sidebar
    await page.click("text=剧本");
    await expect(page).toHaveURL(/\/projects\/[\w-]+\/script/);
  });
});
