# 腾讯隐藏街景：第四轮寻找路径实测

日期：2026-10-07。本报告记录实际成功与失败的请求，不将HTTP200、errno=0或前端字段出现本身视为发现有效全景。

## 1. 新成功路径：scenic_id → photos → svid

腾讯官方前端PanoPhoto.js中的show_region调用配置panoGetPhotoDataUrl，以scenic_id读取景区相册：

https://5gimg.map.qq.com/mappc/public_static/5.2.151/src/Modules/Panorama/PanoPhoto/PanoPhoto.js?ver=v5.2.151

实际可用：

```text
https://sv.map.qq.com/photos?id={scenic_id}&output=json
https://sv.map.qq.com/photos?id={scenic_id}
```

JSON版本响应是GBK，字段detail.scenes。无output版本是UTF-8 XML，字段scene的svid/name/lng/lat/dir/pitch/zoom。最初将XML按GBK解码会乱码，本轮已用UTF-8独立核正。

实测清单：

| scenic_id | 返回scene条数 | 判断 |
|---|---:|---|
|1004-1-501-111222|20|世界之窗旧批次，包含新增夜景种子|
|1004-1-501-111222-2|20|世界之窗2015批次，包含新增J7种子|
|1007-3-0Y6-130304|8|杜甫草堂展示点，小于已查到49点，不是全量目录|
|1007-1-505-052826-2|10|浣花溪公园此分区展示点|
|2007-1-407-315680-1|20|云水谣，从怀远楼至和贵楼|
|1209-1-311-073259-17|17|五台山，含距离原种子较远的望海寺和灵应寺|
|3208-1-410-104264-2|18|崆峒山另一个分区，含三官殿、药王洞等|
|3514-3-1W0-140620|0|五彩滩已有有效全景，但photos无场景|
|3514-3-0W0-140620|0|喀纳斯已有有效全景，但photos无场景|
|1007-1-505-052826|0|building.group_id不能直接替代完整scenic_id|
|1007-1-505-056954|0|同上|
|1209-1-311-073259-1/-2/-3|0|相邻后缀假设失败；不能从空列表断言区域不存在|

云水谣追加count=100仍返回20条。没有找到可靠分页参数，不能声称20是全量或20一定是硬限制。

## 2. 新成功路径：腾讯旧POI UID → xf → 隐藏全景

腾讯官方Panorama.js在getSvidByLatLng里追加uid。本轮验证：

```text
https://sv.map.qq.com/xf?uid=10873500824776957090&output=json
```

无需坐标，返回赛里木湖350630W01406200SCENE001，src=3，get_way=2。

```text
https://sv.map.qq.com/xf?uid=1932968980269003433&output=json
```

无需坐标，返回上海俏江南环球店100235J3140320153524560。

uid=0返回空svid，为负对照。

边界：人祖山7618717683730117123、五彩滩10824788233506854213返回空。杜甫草堂1896716352348137848返回附近草堂路10071018150204153636800（src=1），而非景区点。因此必须单独读取返回ID的/sv确认。

本轮uid来自已知/sv的basic.poi_id，属于机制验证，不是凭空发现新POI。下一步可从合法公开旧POI分享链接、历史页面或正常地图搜索结果获得旧UID。不能把其他地图平台的ID或腾讯现行所有ID格式当作可互换的旧UID。

直接请求当前腾讯POI详情mapsearch?qt=dt&tp=0&uid=...返回403，errMsg=no session，本轮未取得正常搜索会话，不据此声称已经跑通“输入任意景点名称→隐藏全景”。

## 3. 新成功路径：area_id限定的xf查询

官方Panorama.js明确追加plane=1和area_id。五景区采用相同坐标、相同r=50的三组对照：

|景区|普通xf|追加uid|追加plane=1与area_id|
|---|---|---|---|
|赛里木湖|空|350630W01406200SCENE001|350630W01406200SCENE001|
|五彩滩|空|空|空|
|杜甫草堂|空|附近道路10071018150204153636800|100730Y6130304110420800|
|人祖山|空|空|121030J31501070SCENE001|
|上海俏江南环球店|空|100235J3140320153524560|100235J3140320153524560|

复现：

```text
https://sv.map.qq.com/xf?lat=44.608148&lng=81.164692&r=50&area_id=3506-3-0W0-140620&output=json
```

额外消融对照：只加plane=1仍空；只加area_id即可命中赛里木湖；只传area_id而不传坐标则空。本轮支持“景区索引改变检索范围”，不支持“去掉所有限制即可全域扫描”。

这条路径需要已知area_id，所以是景区内寻找/补全工具，不是从零枚举所有景区的方法。尤其当多个scene共用同一坐标时，它可能只返回一个代表点。

## 4. 跨分区photos

前几轮已知崆峒山scenic_id尾数-1、-3，且共享group_id=3208-1-410-104264。本轮有界验证-2，photos返回18个场景；三官殿与药王洞分别独立/sv成功，确实属于-2。

五台山-17的photos则直接带出原种子all_scenes没有给出的远处场景：原种子120930U1131001152420200只有两个附近点，而photos返回望海寺、灵应寺等17个展示点。

这种方法优先测试已经观察到的相邻分区，不应无限枚举尾数；五台山-1/-2/-3本轮没有结果。

## 5. 本轮新增独立验证样本

另见tencent-hidden-streetview-round4-samples.csv。共9个选取的ID，均/sv errno=0且basic.svid与请求一致：

- 10042501111224201012000：世界之窗，埃菲尔铁塔和凯旋门夜景。
- 10042501111224200409000：世界之窗，恺撒宫夜景。
- 100430J7150117112059020：世界之窗，法国罗浮宫玻璃金字塔（接口原名）。
- 100431J7150117131823150：世界之窗，墨西哥巨石头像。
- 120930U1131005131755000：五台山，望海寺。
- 120931U1131005145331100：五台山，灵应寺。
- 320810YF140902125307100：崆峒山，三官殿。
- 320810YF140902135049000：崆峒山，药王洞。
- 200730U3140419134255120：云水谣，和贵楼内景。

其中埃菲尔铁塔夜景、望海寺、三官殿另做普通xf原坐标r=50对照，都返回空；缩略图返回可解码JPEG并实际读取画面。前两张512×256；三官殿768×128，为六面图条带，不是普通经纬展开图。本轮未逐点验证所有候选的完整高分辨率全景。

## 6. 尚未跑通的途径

- rsvids：已根据官方PanoBgPoi.js改用正确region_id参数，仍HTTP406。之前只传svid的失败不能作为正确调用的结论。
- scenic：以景区ID或POI ID等参数测试均406，未取得可用说明数据。
- qxf：仅n参数测试406，缺少完整请求格式，暂不定性接口永久关闭。
- boundinfo：按官方bound=west,north,east,south、level参数测试返回404。
- aroundcustom：官方PanoPhoto.js显示它返回pois[].svid用于附近推荐，但本轮两种坐标请求未取得可用正文，不计入成功路径。
- rarp：源码实际使用lat/lng作逆地址请求，传svid返回空AD不代表能枚举全景；本轮不把它作为ID发现入口。
- Wayback：20180918首页HTML和Index.js已恢复，确认data/index.json与data/special.json及hotScenics字段；对应两个JSON回放明确“has not archived that URL”，未恢复目录。CDX终端请求未拿到正文，也不当不存在证明。

## 7. 推荐实际寻找顺序

1. 起点可为旧pano链接、官方xpconfig、旧POI UID、第三方地点坐标或已知scenic_id。
2. 只有UID：调用xf?uid，再读取返回svid的元数据确认。
3. 有scenic_id：先photos取得展示种子，再按all_scenes、linkpois、region.entrances、history.nodes、trans_svid继续追踪。
4. 有坐标且有scenic_id：调用xf加area_id，补普通道路扫描漏掉的景区点。
5. 有building.group_id及多个已知分区：有界验证相邻scenic_id的photos。
6. 对每个候选分别记录元数据存在、普通空间查询结果、缩略图存在和完整渲染状态。

## 来源

- https://map.qq.com （仍公开的前端配置，仅查看源码）
- https://5gimg.map.qq.com/mappc/public_static/5.2.151/src/Modules/Panorama/Panorama.js?ver=v5.2.151
- https://5gimg.map.qq.com/mappc/public_static/5.2.151/src/Modules/Panorama/PanoPhoto/PanoPhoto.js?ver=v5.2.151
- https://5gimg.map.qq.com/mappc/public_static/5.2.151/src/Modules/Panorama/PanoBgPoi/PanoBgPoi.js?ver=v5.2.151
- https://sv.map.qq.com/photos?id=1209-1-311-073259-17&output=json
- https://sv.map.qq.com/photos?id=3208-1-410-104264-2&output=json
- https://web.archive.org/web/20180918230805/http://map.qq.com/jiejing/home.html
