import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addInitScript(() => {
      localStorage.setItem("scriptforge_onboarding_completed", "true");
    });
  });

  test("page loads with title", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "ScriptForge" })).toBeVisible();
  });

  test("can create a project", async ({ page }) => {
    await page.goto("/");

    // Open create modal
    await page.click("text=新建项目");

    // Fill form
    await page.fill('input[placeholder="例如：长夜将明"]', "E2E 测试项目");
    await page.fill('textarea[placeholder="可选的项目描述"]', "这是一个 E2E 测试项目");

    // Submit
    await page.click("button:has-text('创建'):not(:has-text('第一个'))");

    // Dashboard navigates directly to the new project
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);
  });

  test("project card navigates to project page", async ({ page }) => {
    await page.goto("/");

    // Wait for projects to load
    await page.waitForSelector("text=我的项目");

    // Click first project card if any
    const cards = page.locator("[class*='rounded-xl']").filter({ hasText: /《/ });
    const count = await cards.count();

    if (count > 0) {
      await cards.first().click();
      // Should navigate to project page
      await expect(page).toHaveURL(/\/projects\/[\w-]+/);
    }
  });
});
