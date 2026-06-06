import { test, expect } from "@playwright/test";

test.describe("Characters and Versions", () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addInitScript(() => {
      localStorage.setItem("scriptforge_onboarding_completed", "true");
    });
  });

  test("creates a character and a relationship", async ({ page }) => {
    await page.goto("/");

    // Create project
    await page.click("text=新建项目");
    await page.fill('input[placeholder="例如：长夜将明"]', "角色关系测试项目");
    await page.click("button:has-text('创建'):not(:has-text('第一个'))");
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);

    // Navigate to characters page via URL
    const projectUrl = page.url();
    const projectIdMatch = projectUrl.match(/\/projects\/([\w-]+)/);
    expect(projectIdMatch).toBeTruthy();
    const projectId = projectIdMatch![1];
    await page.goto(`/projects/${projectId}/characters`);
    await expect(page.locator("text=角色管理")).toBeVisible();

    // Create first character (fill the form, then save — create-on-save)
    await page.click("text=新建角色");
    await page.fill("#char-name", "张三");
    await page.getByRole("button", { name: "保存" }).click();
    await expect(page.getByText(/角色.*已创建/)).toBeVisible({ timeout: 10000 });

    // Create second character
    await page.click("text=新建角色");
    await page.fill("#char-name", "李四");
    await page.getByRole("button", { name: "保存" }).click();
    await expect(page.getByText(/角色.*已创建/)).toBeVisible({ timeout: 10000 });

    // Select first character and add relationship
    await page.locator("[data-char-id]").first().click();
    await page.click("text=添加");
    // The dropdown contains the other character; select by value (second option)
    const options = page.locator("select").first().locator("option");
    const otherOption = options.nth(1);
    const otherValue = await otherOption.getAttribute("value");
    if (otherValue) {
      await page.locator("select").first().selectOption(otherValue);
    }
    await page.click("text=创建");

    await expect(page.getByText("关系已创建")).toBeVisible({ timeout: 10000 });

    // Navigate to graph tab and verify an edge is rendered
    await page.click("text=关系图");
    await expect(page.locator(".react-flow__edge")).toHaveCount(1, { timeout: 10000 });
  });

  test("version history loads from API", async ({ page }) => {
    await page.goto("/");

    // Create project
    await page.click("text=新建项目");
    await page.fill('input[placeholder="例如：长夜将明"]', "版本测试项目");
    await page.click("button:has-text('创建'):not(:has-text('第一个'))");
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);

    const projectUrl = page.url();
    const projectIdMatch = projectUrl.match(/\/projects\/([\w-]+)/);
    expect(projectIdMatch).toBeTruthy();
    const projectId = projectIdMatch![1];
    await page.goto(`/projects/${projectId}/versions`);

    await expect(page.locator("text=版本历史")).toBeVisible();
    // Either empty state or loaded list; demo data should be gone
    await expect(page.locator("text=暂无版本记录")).toBeVisible();
  });
});
