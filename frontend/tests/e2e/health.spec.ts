import { test, expect } from "@playwright/test";

test.describe("health endpoint", () => {
  test("returns healthy response", async ({ request }) => {
    const response = await request.get("/api/health");
    expect(response.ok()).toBeTruthy();
  });
});
