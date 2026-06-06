import { test, expect } from "@playwright/test";

test.describe("Project workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addInitScript(() => {
      localStorage.setItem("scriptforge_onboarding_completed", "true");
    });
  });

  test("upload chapter via textarea", async ({ page }) => {
    await page.goto("/");

    // Create a project first
    await page.click("text=新建项目");
    await page.fill('input[placeholder="例如：长夜将明"]', "章节测试项目");
    await page.click("button:has-text('创建'):not(:has-text('第一个'))");

    // Should be on chapters page after creation
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);
    await expect(page.locator("text=章节管理")).toBeVisible();

    // Add chapter via header button
    await page.getByRole("button", { name: "添加章节" }).click();
    await page.fill('input[placeholder="例如：第一章·离别"]', "第一章");
    await page.fill('textarea[placeholder="粘贴小说章节内容…"]', "这是第一章的内容。主角登场。");
    await page.locator('button[type="submit"]').click();

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

    // Navigate to script editor via URL (sidebar is icon-only on desktop)
    const projectUrl = page.url();
    const projectIdMatch = projectUrl.match(/\/projects\/([\w-]+)/);
    expect(projectIdMatch).toBeTruthy();
    const projectId = projectIdMatch![1];
    await page.goto(`/projects/${projectId}/script`);

    await expect(page).toHaveURL(/\/projects\/[\w-]+\/script/);
  });
});
