import { readFileSync } from "node:fs";

const appSource = readFileSync("apps/web/src/pages/App.tsx", "utf8");

const checks = [
  {
    name: "ContactsPanel derives an employee-only contact list",
    pass: /const employeeContacts = all\.filter\(\s*\(item\) => item\.contact_type === "user"\s*\)/s.test(
      appSource
    )
  },
  {
    name: "ContactsPanel labels the second group as employee contacts",
    pass: appSource.includes("<Typography.Text type=\"secondary\">员工联系人</Typography.Text>")
  },
  {
    name: "ContactsPanel renders the second list from employeeContacts",
    pass: /dataSource=\{employeeContacts\}/.test(appSource)
  },
  {
    name: "ContactsPanel no longer labels the second group as all contacts",
    pass: !appSource.includes("<Typography.Text type=\"secondary\">全部联系人</Typography.Text>")
  }
];

const failed = checks.filter((check) => !check.pass);
if (failed.length) {
  console.error("Frontend contacts dedup regression failed:");
  for (const check of failed) {
    console.error(`- ${check.name}`);
  }
  process.exit(1);
}

console.log("Frontend contacts dedup regression passed.");
