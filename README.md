# tencent-hidden-pano-data

腾讯地图隐藏街景（非道路采集全景：景区步采、室内、商家、第三方与特殊项目）的研究数据与工具集合。

Research data and tools for Tencent Maps hidden panoramas (non-road-coverage street view).

## 目录结构

```text
docs/                 调查报告（第二轮至第五轮、遍历报告、论坛考古）
data/                 样本清单 CSV（杜甫草堂、各轮新增、遍历结果、论坛 2773 条）
data/raw/             原始数据（论坛页面提取 JSON、验证证据 JSON）
tools/                可复跑脚本与官方旧配置备份
sansha-streetview/    三沙历史街景离线恢复包（含全景图、六面图与离线查看器）
```

## 核心文件

| 文件 | 内容 |
| --- | --- |
| `data/tencent-forum-4391-combined.csv` | 官方论坛《腾讯地图·景点大全》两页去重后 2773 个历史 PanoID |
| `data/tencent-enumeration-results.csv` | 遍历爬取法实测 151 个有效全景 ID |
| `data/tencent-hidden-streetview-dufu-49.csv` | 杜甫草堂 49 个场景 ID |
| `data/tencent-hidden-streetview-round2-additional.csv` | 金草滩 / 五彩滩 / 浣花溪公园 / 四川博物院样本 |
| `data/tencent-panoid-round3-samples.csv` | 第三轮样本（人祖山 / 云水谣 / 世界之窗夜景等） |
| `data/tencent-hidden-streetview-round4-samples.csv` | 第四轮样本（五台山 / 崆峒山等） |
| `data/tencent-hidden-streetview-round5-uids.csv` | 历史 POI UID 反查结果（29 条，含空结果） |
| `data/tencent-hidden-streetview-round5-albums.csv` | 景区相册扩展 40 条 |
| `docs/tencent-hidden-streetview-round4-routes.md` | photos / uid / area_id 三大入口链路说明 |
| `docs/tencent-forum-wayback-findings.md` | 论坛考古方法与 7Q / 三沙 / XTY 发现 |
| `tools/tencent-enumeration.py` | 可复跑的 ID 遍历脚本（断点续查、限速、日志） |
| `tools/tencent-xpconfig-source.js` | 腾讯官方旧城市推荐配置备份 |

## 工具用法

```text
python tools/tencent-enumeration.py tools/tencent-enumeration-plan.json --dry-run
python tools/tencent-enumeration.py tools/tencent-enumeration-plan.json --limit 110
python tools/tencent-enumeration.py tools/tencent-enumeration-plan.json --audit
```

## 三沙离线查看器

打开 `sansha-streetview/三沙街景-离线查看.html` 即可离线查看四个恢复的三沙历史全景（三沙市政府、西沙海洋博物馆门口、西沙宾馆大堂、老龙头祖国万岁礁）。技术要点见 `sansha-streetview/README.md`。

## 数据说明与验证口径

- 全部 ID 来自腾讯公开接口（`sv.map.qq.com`）的实际查询，验证程度分为：元数据有效 / 缩略图存在 / 可完整渲染，三者分开记录。
- `data/tencent-forum-4391-combined.csv` 中的 2773 个 ID 为历史链接库存，**未全量验证**。
- 隐藏全景需要通过 ID 直接访问，例如：`https://qq-map.netlify.app/#pano={PanoID}`。

## 免责声明

影像与数据的版权属于原权利人（腾讯公司及相关采集方）。本仓库仅用于历史影像的研究与存档，请在合法合规的范围内使用。
