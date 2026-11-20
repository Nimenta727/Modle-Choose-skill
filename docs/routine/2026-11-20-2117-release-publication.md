# 2026-11-20 21:17 (+08:00) — 触发候选版发行 / Trigger prerelease publication

## 中文

### 修改
- 完整 CI 通过后新增发行标记，触发 v2.3.0-rc.1 GitHub Release 工作流。
- 发布资产应包含独立 Skill ZIP、SHA-256 校验文件和中英文发行说明。
- 本次提交不改动模型路由和执行权限规则。

### 验证与下一步
- 先前完整 CI 已通过：https://github.com/Nimenta727/Modle-Choose-skill/actions/runs/44739504040
- 发布工作流需再次验证。只有发布成功后才能宣称 Release 已创建。
- 下一步核对 Release 页面、附件和校验和；再在真实客户端进行端到端测试，由所有者决定项目许可证。

## English

### Changes
- Added a deliberate v2.3.0-rc.1 publication marker after the full CI suite succeeded.
- The workflow must attach standalone Skill ZIP, SHA-256 and bilingual release notes.
- This commit does not change routing behavior or execution permissions.

### Verification and next steps
- Prior successful CI: https://github.com/Nimenta727/Modle-Choose-skill/actions/runs/44739504040
- The release workflow must still succeed before publication can be claimed.
- Next: verify Release page and assets, perform authenticated-client integration and let the owner choose the license.
