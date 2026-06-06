import { test, expect } from "@playwright/test";

/**
 * End-to-end workflow test covering the full user journey:
 * create project → upload 3 chapters → configure provider
 * → start conversion → verify scene timeline → edit dialogue
 * → checkpoint → export YAML.
 *
 * The backend conversion pipeline and script editor data loading
 * are not yet fully wired, so this test uses page.route() to mock
 * the SSE conversion stream and export endpoint while exercising
 * real backend APIs for project/chapter/provider CRUD.
 */

test.describe("Full conversion workflow", () => {
  test("completes project → conversion → edit → export journey", async ({
    page,
  }) => {
    const timestamp = Date.now();
    const projectName = `E2E 完整流程 ${timestamp}`;

    // ── 1. Visit dashboard and create project ──
    // Skip onboarding wizard by marking it completed before navigation
    await page.context().addInitScript(() => {
      localStorage.setItem("scriptforge_onboarding_completed", "true");
    });
    await page.goto("/");

    await page.click("text=新建项目");
    await page.fill('input[placeholder="例如：长夜将明"]', projectName);
    await page.fill('textarea[placeholder="可选的项目描述"]', "E2E 测试项目描述");
    await page.click("button:has-text('创建'):not(:has-text('第一个'))");

    // ── 2. Add 3 chapters ──
    // Dashboard navigates directly to the new project after creation
    await expect(page).toHaveURL(/\/projects\/[\w-]+/);
    await expect(page.locator("text=章节管理")).toBeVisible();

    const chapters = [
      { title: "第一章：雨夜访客", text: "雨下得很大。主角走进一家旧书店，老板抬起头看了他一眼。" },
      { title: "第二章：秘密信件", text: "主角在书店角落发现一封泛黄的信件，信封上没有署名。" },
      { title: "第三章：真相浮现", text: "信中的内容揭示了一个隐藏多年的秘密，主角决定追查下去。" },
    ];

    for (const ch of chapters) {
      await page.getByRole("button", { name: "添加章节" }).click();
      await page.fill('input[placeholder="例如：第一章·离别"]', ch.title);
      await page.fill('textarea[placeholder="粘贴小说章节内容…"]', ch.text);
      await page.locator('button[type="submit"]').click();
      await expect(page.locator(`text=${ch.title}`)).toBeVisible();
    }

    // ── 3. Configure LLM provider ──
    // Sidebar shows icon-only on desktop; navigate by URL instead
    const projectUrl = page.url();
    const projectIdMatch = projectUrl.match(/\/projects\/([\w-]+)/);
    expect(projectIdMatch).toBeTruthy();
    const projectId = projectIdMatch![1];
    await page.goto(`/projects/${projectId}/providers`);
    await expect(page.getByRole("heading", { name: "模型配置" })).toBeVisible();

    await page.click("text=添加模型");
    await page.fill('input[type="text"] >> nth=0', "E2E Test Provider");
    await page.fill('input[type="text"] >> nth=1', "gpt-4o-mini");
    await page.fill('input[type="password"]', "sk-test-key");

    // Assign all three stages
    await page.click("text=圣经分析");
    await page.click("text=章节转换");
    await page.click("text=剧本组装");

    await page.locator('form button[type="submit"]').click();
    await expect(page.locator("text=E2E Test Provider")).toBeVisible();

    // ── 4. Start conversion with mocked SSE stream ──
    await page.goto(`/projects/${projectId}/convert`);
    await expect(page.locator("text=AI 转换流水线")).toBeVisible();

    // Intercept SSE stream and return fake progress events
    await page.route("**/api/projects/*/convert/stream", async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
        },
        body: [
          'data: {"current_stage":"validate_input","percent":5,"message":"验证输入..."}\n\n',
          'data: {"current_stage":"stage_0_bible","percent":30,"message":"正在分析故事圣经..."}\n\n',
          'data: {"current_stage":"stage_1_chapter","percent":60,"message":"正在转换章节..."}\n\n',
          'data: {"current_stage":"stage_2_assemble","percent":85,"message":"正在组装剧本..."}\n\n',
          'data: {"current_stage":"format_output","percent":95,"message":"正在格式化输出..."}\n\n',
          'data: {"current_stage":"done","percent":100,"message":"转换完成"}\n\n',
          "event: close\ndata: \n\n",
        ].join(""),
      });
    });

    // Intercept runs list to return a completed run
    await page.route("**/api/projects/*/convert/runs", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([
          {
            id: "run-e2e-001",
            status: "completed",
            stage: "format_output",
            error_message: null,
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            duration_seconds: 12,
          },
        ]),
      });
    });

    await page.click("text=开始转换");

    // Verify progress reaches 100%
    await expect(page.getByText("100%").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("转换完成").first()).toBeVisible();

    // ── 5. Navigate to script editor and verify scene timeline ──
    await page.goto(`/projects/${projectId}/script`);
    await expect(page).toHaveURL(/\/projects\/[\w-]+\/script/);

    // Scene timeline should render scene cards (demo script has 3 scenes)
    await expect(page.getByText("#1").first()).toBeVisible();
    await expect(page.getByText("#2").first()).toBeVisible();
    await expect(page.getByText("#3").first()).toBeVisible();

    // ── 6. Edit a dialogue block ──
    const firstDialogue = page.locator('[data-testid="dialogue-line"]').first();
    await firstDialogue.scrollIntoViewIfNeeded();
    await firstDialogue.click({ force: true });
    await firstDialogue.fill("这是修改后的对白内容。");
    await firstDialogue.press("Escape");

    // Verify the edited text persists in the DOM
    await expect(page.locator("text=这是修改后的对白内容。")).toBeVisible();

    // ── 7. Trigger checkpoint via Command Palette ──
    let checkpointRequested = false;
    await page.route("**/api/projects/*/versions/checkpoint", async (route, request) => {
      checkpointRequested = true;
      const postData = request.postDataJSON();
      expect(postData).toHaveProperty("yaml_content");
      expect(postData).toHaveProperty("message");
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "Checkpoint created",
          version_id: "v-e2e-001",
        }),
      });
    });

    await page.keyboard.press("Meta+k");
    await page.click("text=创建存档点");
    await page.fill('input[placeholder*="存档"]', "E2E 测试检查点");
    await page.click("text=保存存档");

    await expect.poll(() => checkpointRequested).toBe(true);

    // ── 8. Export YAML ──
    let exportRequested = false;
    await page.route("**/api/projects/*/export/yaml", async (route) => {
      exportRequested = true;
      await route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "text/yaml",
          "Content-Disposition": 'attachment; filename="e2e-script.yaml"',
        },
        body: "schema_name: scriptforge-script\nmetadata:\n  title: E2E Test Script\n",
      });
    });

    await page.click('button[title="导出剧本"]');
    await page.click("text=YAML");
    await page.click('button:has-text("导出")');

    await expect.poll(() => exportRequested).toBe(true);
  });
});
