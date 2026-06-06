import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("page loads with title", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=ScriptForge")).toBeVisible();
  });

  test("can create a project", async ({ page }) => {
    await page.goto("/");

    // Open create modal
    await page.click("text=新建项目");

    // Fill form
    await page.fill('input[placeholder="项目名称"]', "E2E 测试项目");
    await page.fill('textarea', "这是一个 E2E 测试项目");

    // Submit
    await page.click("text=创建");

    // Should see the project card
    await expect(page.locator("text=E2E 测试项目")).toBeVisible();
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
