# 腾讯隐藏街景第二轮调查：我秀中国线索与场景关联

调查会话日期：2026-10-07。结论是本轮实际返回状态；接口未来可能变化。

## 结果与验证范围

- 杜甫草堂：49 个不同 ID，逐个验证 metadata，全部 scenic_id=1007-3-0Y6-130304，入口图片实际加载成功。
- 浣花溪公园：12 个不同 ID，逐个验证 metadata，分属同一 building.group_id 的两个 scenic_id。
- 四川博物院：10 个不同 ID，逐个验证 metadata，分属同一 building.group_id 的两个 scenic_id。
- 阿拉尔金草滩民俗园：3 个不同 ID，逐个验证 metadata，SCENE001 图片实际加载成功。
- 五彩滩：7 个不同 ID，逐个验证 metadata，SCENE001 图片实际加载成功；008、009 返回 errno=-1。
- 总计 81 个不同景区 ID。不是 81 张均已验证可渲染；CSV verification 字段记录了具体验证级别。
- 普通空间查询 /xf 在杜甫草堂两个点、浣花溪公园两个点、金草滩及五彩滩代表点的原始元数据坐标处，r=50 返回空 svid。其余点没有逐个进行空间排除测试。
- 杜甫草堂 49 点是本次沿给定前缀的关联闭包，不保证腾讯库中该景区再无其他版本或孤立节点。

CSV 文件：

- tencent-hidden-streetview-dufu-49.csv
- tencent-hidden-streetview-round2-additional.csv（32 条）

## 我秀中国可用的一手来源

1. http://streetview.ishowchina.com/
2. http://streetview.ishowchina.com/virtualTourism.htm
3. http://streetview.ishowchina.com/js/citylist.js
4. http://map.ishowchina.com/js/jsmap/jsurl.js
5. http://map.ishowchina.com/js/street.js
6. http://public.ishowchina.com/H5/ishow.pano.437585ac7750fe3f6d9afc786ca14610.js

首页与旅游页公开保存 c=城市行政代码、s=StationID 的链接。完整地图入口在本次浏览器中跳转登录页，但公开页面、脚本及部分只读场景接口能正常读取。未执行登录或使用账号操作。

citylist.js 引用城市目录 /city/getOrderCity 和推荐列表 /recommendation/getListByCity，并使用 qid、stationId、pointName、viewpic 字段。本次 www.ishowchina.com 的目录/推荐列表请求返回空正文，包括一个带 callback 参数的请求；不能把 HTTP 200 视为恢复成功。

实际可用接口：

```text
http://streetapi.ishowchina.com/property/i/{StationID}
http://streetapi.ishowchina.com/property/nearby?lonlat={lng},{lat}&pageSize=3&range=200
http://streetapi.ishowchina.com/property/nearest?lonlat={lng},{lat}&pageSize=3&range=200
http://streetapi.ishowchina.com/property/history/nearby?lonlat={lng},{lat}&pageSize=3&range=200&not=false&page=1
```

HTTP 版本实际成功；HTTPS 版本的一次请求超时，不表示所有 HTTPS 路径必然失效。

字段：StationID；Address；L/B；LonLatShape.X/Y；CityCode；VID；DataType；Previous/Next；SegmentGuid；SortIDX；Camera；JunctionItems；部分样本有 range[].obj[].id。

不要混淆 CityCode 与分享链接 c：抚顺分享链接 c=210400，而属性 CityCode=0413。腾讯地区前缀为另一套编号（本次道路样本1404）。

原始 X/Y 是另外一组大数值，不能直接当经纬度；本次跨站地理线索使用 L/B。未建立两站全部数据的坐标基准等价关系，位置近似命中不构成同源图片证明。

## 我秀 ID 的有限样本规律

上海这一批 DataType=D 样本支持下述序号关系：

```text
100021-0-20090427 + HHMMSS + NNNN
HHMMSS = 01:00:00 加 NNNN 秒
```

三个根据规律生成且有效的独立样本：

| ID | 地点 | N |
|---|---|---|
| 100021-0-200904270101000060 | 八仙台 | 60 |
| 100021-0-200904270101010061 | 鸳鸯楼 | 61 |
| 100021-0-200904270102000120 | 上海新国际博览中心 | 120 |

反例对照：100021-0-200904270101000061 与 100021-0-200904270101010060 均返回 s_1002（站点信息不存在）。抚顺相邻序号25/26分别是东林公园、平顶山惨案纪念馆，地理上不连续。

因此，这一批时间样尾段很可能包含人工排序编码，不能当真实拍摄时间。未证明全部 D 型遵循此规则。北京道路 C 型 000288-0-200907090051090932 则有真实的 Previous/Next、SegmentGuid、SortIDX 和邻接ID；不要把 D 型规则套到 C 型。

Time 在本次若干 D 样本中为 null；TotalNum 在多个城市的 D 样本中重复4565，不能当每个景区的场景数。

## 跨站寻找成功的证据链

我秀旅游页：杜甫草堂，StationID=100028-0-201110200101110071。

属性接口：
http://streetapi.ishowchina.com/property/i/100028-0-201110200101110071

返回 Address=杜甫草堂-南门，L=104.028734，B=30.659575。

直接在这一坐标查询腾讯 r=300、r=2000 均未返回ID。转向附近草堂路，以 104.025,30.66、r=500 查询成功：
https://sv.map.qq.com/xf?lat=30.66&lng=104.025&r=500&output=json

返回道路ID 10071018150204153656500。其属性：
https://sv.map.qq.com/sv?svid=10071018150204153656500&output=json

包含入口 reid=100730Y6130304110420800，name=杜甫草堂。独立查询该景区ID返回 park、source=soso、scenic_id=1007-3-0Y6-130304，并在查看器实际显示图片。

https://qq-map.netlify.app/#pano=100730Y6130304110420800

本次没有发现 StationID→腾讯ID 的直接映射字段。把抚顺原始StationID及其去连字符版本直接传给腾讯 /sv 均失败。同一地点不等于同一照片、同一采集批次，也不能用这条地理链证明两家公司共享底层影像。

其他地理对照：

- 我秀东林公园 100413-0-201011150100250025 → 腾讯附近东林路 14041022130621103242100，普通可扫描道路，未返回隐藏入口。
- 我秀五彩池 100837-0-201010190100070007 → 腾讯附近 281810C1131025104600000，普通可扫描街景，type=street/source=soso，不列入81个隐藏景区候选清单。
- 我秀上海老城隍庙、杭州灵隐寺样本本次未找到可确认的腾讯隐藏对应点。上海扩大半径只返回其他道路点，不能冒称景区匹配。

## 新的腾讯关联规律

### all_scenes 是局部列表，递归才能扩展

草堂正门初始列表35项；从另一个内部点可得到46项；沿真实返回ID逐项读取，最终得到49个不同ID，所有主记录具有相同 scenic_id。

探索中额外返回100735W6150120154732890、100733W6150120145152000；独立查询发现它们属于成都浣花溪公园。通过 all_scenes 与 linkpois 继续追踪，又连接到四川博物院。

不要将每个响应的列表长度当景区总数，也不要将坐标相同的不同ID合并。

### linkpois[].svid 是额外的跨场景入口

https://sv.map.qq.com/sv?svid=100735W6150120154732890&output=json

其中 linkpois 列出诗歌大道、新诗小径、湿地木桥道。新诗小径100734W6150120151958670不在该响应的all_scenes中，却能独立查询成功。

### history.nodes 能找回保留更多入口信息的道路版本

2015道路10071018150204153656500返回杜甫草堂入口，并在history.nodes列出2012道路10071003121026124549800。
2012版本本次没有region，all_scenes为空；history.nodes仍指回2015版本。因此拿到旧道路种子时，应读取其历史版本，而不能看到空列表就结束。

### 同一景区有多个入口，入口与默认退出点未必一一互反

杜甫草堂入口1：reid=100730Y6130304110420800，道路svid=10071018150204153638100。
入口2：reid=100730Y6130304173723000，道路svid=10071018150204153549500。
后者景区点自己的basic.quit_svid仍为入口1的道路。故应分别保存入口边、退出边，不能合并为单一双向关系。

### W6 前缀与 scenic_id 不是一一对应

同日同W6系列跨浣花溪公园与四川博物院。前三位代码30W6/31W6对应本批博物院记录，32W6至36W6对应本批公园不同位置，但未证明这是通用排序语义。

building.group_id 给出另一层分组：

- 成都浣花溪公园：1007-1-505-052826，scenic_id后缀-1和-2。
- 四川博物院：1007-1-505-056954，scenic_id后缀-1和-2。

floors数组存在，但本次名称与svid为空，不能说找到了可用楼层入口；不能把scenic_id尾数武断解释为实际楼层号。

## 渲染状态与仍存图片

诗歌大道100735W6150120154732890在qq-map查看器中显示元数据，但场景黑屏及切片错误图标。直接缩略图返回真实的六面图条带：

https://sv1.map.qq.com/thumb?from=web&svid=100735W6150120154732890&level=0&x=0&y=0

四川汉代陶石艺术馆也返回真实室内缩略图：

https://sv1.map.qq.com/thumb?from=web&svid=100731W6150120133757940&level=0&x=0&y=0

W6样本detail.tile.proj_type=0，hd为2行12列，ud为4行24列，每片896×896，并有start_scan/end_scan/total_scan字段。与上一轮查看器硬编码的512像素、8×4/16×8等普通全景布局不同。已确认缩略图存在以及查看器渲染失败；没有完成这种格式的全分辨率重建。

type=indoor 也用于户外诗歌大道，不能据字面确定拍摄环境。

我秀东林公园缩略图则返回HTTP200的JSON错误：s_2002，影像库不存在指定图片。其metadata存在不等于影像存在。

## 新疆结果与失败边界

金草滩民俗园351032W01408110SCENE001—003分别为浮雕壁画、栈道上1、栈道上2，三点逐个成功。
五彩滩351431W01406200SCENE001—007逐个成功，008、009失败；001的all_scenes为空。未验证010以后，不推断有永久连续边界。

有限高序号验证：3501/140829、3503/140811、3510/140811、3508/140811四组分别测试6、7、A；3514/140620测试6、A；3506/140620测试6，均为SCENE001，15个候选均返回errno=-1。没有新证据扩大新疆景区代码0—5范围，也不能由少量失败证明高代码不存在。

## 后续建议

1. 先用第三方历史地点目录找地理种子，再到腾讯附近道路提取入口；保留地点对应与同图对应的证据区别。
2. 腾讯元数据同时提取all_scenes、region.entrances、linkpois、history.nodes、basic.quit_svid、basic.trans_svid；building.floors[].svid仅在实际非空时使用。
3. 以完整ID去重，以scenic_id及building.group_id辅助归属；记录有向入口/退出边。
4. 对SCENE列表缺失的批次做有界序号验证；不要将接口超时当不存在。
5. W6样本优先研究detail.tile与现存缩略图的布局，避免把查看器黑屏误记成资源丢失。
