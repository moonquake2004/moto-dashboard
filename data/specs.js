/* 车型技术参数（选购向）
   数据源：摩托范（58moto）「参数配置」页逐款抓取，键为「品牌名|车型名」，与 dashboard.js 的 model.name 对齐。
   口径：同款有多个配置版本时，取官方指导价对应的版本（默认最新年款标准配置），variant 字段标注实际取值版本。
   未抓到的字段一律缺省（前端显示「—」），不做估算填充。 */
window.MOTO_SPECS = {
  meta: {
    asOf: "2026-11-14",
    source: "摩托范（58moto）参数配置页",
    sourceNote: "逐款抓取，标注 variant 为实际取值版本；同款多配置时取官方指导价对应版本",
    totalModels: 438
  },
  models: {
    "春风|500SR": {
      variant: "2026款 500SR 电子油门版", price: "31,580",
      kw: 58, kwRpm: 12500, nm: 49, nmRpm: 10000, cc: 500, cyl: "四缸",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "铬钼钢编织车架",
      lwh: "2010x720x1185", seat: 805, wb: 1395, tank: 15.5, weight: 189,
      suspF: "倒置式 φ41mm，预载/压缩/回弹可调", suspR: "中置式多连杆减震",
      brkF: "300mm 双碟 · 对置四活塞（NISSIN）", brkR: "220mm 单碟 · 浮动单活塞",
      tireF: "120/70-ZR17", tireR: "160/60-ZR17",
      abs: "标配前后", tcs: "标配可关闭", qs: "标配双向", cruise: "标配",
      tpms: "标配", keyless: "无", dash: "6.2 英寸 TFT",
      src: "https://www.58moto.com/good/22644/configuration.html"
    },
    "春风|450SR": {
      variant: "2026款 450SR", price: "23,980",
      kw: 38, kwRpm: 9500, nm: 40, nmRpm: 7750, cc: 450, cyl: "双缸", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钢管编织车架",
      lwh: "1990x715x1165", seat: 795, wb: 1365, tank: 14, weight: 170, clearance: 145,
      suspF: "φ37mm 倒置式", suspR: "中置式多连杆减震",
      brkF: "φ320mm 单碟 · 对置四活塞（Brembo）", brkR: "φ220mm 单碟 · 单活塞",
      tireF: "110/70-R17", tireR: "150/60-R17",
      src: "https://www.58moto.com/good/19912/configuration.html"
    },
    "凯越|450RR": {
      variant: "2026款 450RR 曼岛Ⅱ", price: "25,777",
      kw: 52, kwRpm: 13250, nm: 39, nmRpm: 11000, cc: 450, cyl: "四缸", cmp: "11.6:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "HC700+Q355B 编织车架",
      lwh: "2015x740x1090", seat: 785, wb: 1385, tank: 15, weight: 165,
      suspF: "KYB 倒置式 φ41mm", suspR: "中置式单减震（内置气囊 · KYB）",
      brkF: "300mm 双浮动盘 · 对置四活塞（泰斯克）", brkR: "220mm 单碟 · 单活塞（泰斯克）",
      tireF: "120/70-ZR17", tireR: "160/60-ZR17",
      abs: "标配前后",
      src: "https://www.58moto.com/good/19844/configuration.html"
    },
    "赛科龙|RT450": {
      variant: "2027款 RT450", price: "32,980",
      kw: 31.5, kwRpm: 8100, nm: 44.2, nmRpm: 5600, cc: 400, cyl: "双缸", cmp: "11:1",
      cool: "水冷", gear: "CVT 无级变速", clutch: "干式离心式离合", drive: "皮带传动",
      frame: "双摇篮车架",
      lwh: "2230x770x1395", seat: 780, wb: 1525, tank: 18, weight: 210, clearance: 135,
      suspF: "正置式", suspR: "边置式双减震（外置气囊 · 预载可调）",
      brkF: "盘式 · 西互卡钳", brkR: "盘式 · 日清卡钳",
      tireF: "120/70-15", tireR: "140/70-14",
      abs: "标配前后", tcs: "标配", qs: "无", cruise: "无", tpms: "标配",
      keyless: "标配 NFC/RFID", dash: "TFT 仪表",
      src: "https://www.58moto.com/good/22897/configuration.html"
    },
    "本田|NSS350": {
      variant: "2026款 NSS350 标准版", price: "40,880",
      kw: 21.6, kwRpm: 7500, nm: 31.8, nmRpm: 5500, cc: 350, cyl: "单缸", cmp: "10.5:1",
      cool: "水冷", gear: "CVT 无级变速", clutch: "干式离心式离合", drive: "皮带传动",
      lwh: "2143x754x1387", seat: 780, wb: 1510, tank: 11.7, weight: 186, clearance: 140,
      suspF: "正置式", suspR: "边置式双减震",
      brkF: "盘式", brkR: "盘式",
      tireF: "120/70-15", tireR: "140/70-14",
      abs: "标配前后", tcs: "标配",
      src: "https://www.58moto.com/good/20281/configuration.html"
    },
    "无极|SR450X": {
      variant: "2026款 SR450X", price: "34,980",
      kw: 31, kwRpm: 7500, nm: 42, nmRpm: 5750, cmp: "11:1",
      cool: "水冷", gear: "CVT 无级变速", drive: "皮带传动",
      lwh: "2175x885x1395", seat: 795, wb: 1525, tank: 18, weight: 210, clearance: 180,
      suspF: "KYB 倒置式", suspR: "边置式双减震（外置气囊 · 预载/阻尼可调）",
      brkF: "φ300mm 浮动单碟 · 对四活塞（西互）", brkR: "φ240mm 单碟 · 单活塞（日信）",
      tireR: "150/70-14",
      src: "https://www.58moto.com/good/22474/configuration.html"
    },
    "春风|675SR-R": {
      variant: "2026款 675SR-R", price: "39,580",
      kw: 70, kwRpm: 11000, nm: 70, nmRpm: 8250, cc: 675, cyl: "三缸", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "铬钼合金钢编织车架",
      lwh: "2020x728x1105", seat: 810, wb: 1400, tank: 15, weight: 195, clearance: 140,
      suspF: "KYB 倒置式 · 18 段可调", suspR: "KYB 中置 · 预载阻尼可调",
      brkF: "φ300mm 双碟 · 四活塞辐射式（西互）", brkR: "φ240mm 单碟 · 单活塞",
      tireF: "120/70-ZR17", tireR: "180/55-ZR17",
      src: "https://www.58moto.com/good/20859/configuration.html"
    },
    "无极|CU250": {
      variant: "2026款 CU250 Ⅱ代 手动挡", price: "16,480",
      kw: 20, kwRpm: 9000, nm: 23, nmRpm: 7000, cc: 250, cyl: "双缸 V型", cmp: "12:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "皮带传动",
      frame: "钢管编织车架",
      lwh: "2200x820x1090", seat: 710, wb: 1460, tank: 15, weight: 178, clearance: 175,
      suspF: "倒置式", suspR: "边置式双减震",
      src: "https://www.58moto.com/good/21252/configuration.html"
    },
    "本田|ADV350": {
      variant: "2026款 ADV350 标准版", price: "42,380",
      kw: 21.6, kwRpm: 7500, nm: 31.8, nmRpm: 5500, cc: 350, cyl: "单缸", cmp: "10.5:1",
      cool: "水冷", gear: "CVT 无级变速", clutch: "干式离心式离合", drive: "皮带传动",
      lwh: "2200x895x1385", seat: 795, wb: 1518, tank: 11.7, weight: 188, clearance: 155,
      suspF: "KYB 倒置式（行程 125mm）", suspR: "边置式双减震（外置气囊 · KYB · 行程 130mm）",
      brkF: "φ256mm 单盘", brkR: "φ240mm 单盘",
      tireF: "120/70-15", tireR: "140/70-14",
      abs: "标配前后", tcs: "标配",
      src: "https://www.58moto.com/good/21727/configuration.html"
    },
    "无极|CU625": {
      variant: "2026款 CU625 自动挡", price: "27,980",
      kw: 45, kwRpm: 8500, nm: 61, nmRpm: 5500, cc: 600, cyl: "双缸 V型", cmp: "12:1",
      cool: "水冷", gear: "AMT 6 速自动挡", clutch: "湿式多片滑动离合", drive: "皮带传动",
      frame: "钢管摇篮式车架",
      lwh: "2315x860x1105", seat: 710, wb: 1525, tank: 16, weight: 215, clearance: 165,
      suspF: "倒置式", suspR: "边置式双减震",
      tireF: "130/90-R16", tireR: "150/80-R16",
      src: "https://www.58moto.com/good/21527/configuration.html"
    },
    "春风|800NK": {
      variant: "2025款 800NK", price: "42,580",
      kw: 74, kwRpm: 9000, nm: 81, nmRpm: 8000, cc: 800, cyl: "双缸 直列", cmp: "12.7:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      lwh: "2146x818x1120", seat: 795, wb: 1468, tank: 15, weight: 186,
      suspF: "KYB 倒置式 · 多段可调", suspR: "KYB 中置单减 · 多段可调",
      brkF: "φ320mm 双碟 · 辐射式卡钳（西互）", brkR: "φ260mm 单碟（西互）",
      tireF: "120/70-ZR17", tireR: "180/55-ZR17",
      abs: "标配前后", tcs: "标配", qs: "标配双向", cruise: "标配",
      src: "https://www.58moto.com/good/20308/configuration.html"
    },
    "春风|450CL-C": {
      variant: "2026款 450CL-C", price: "21,980",
      kw: 30, kwRpm: 8000, nm: 42, nmRpm: 6250, cc: 450, cyl: "双缸 直列", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "皮带传动",
      frame: "钢管编织车架",
      lwh: "2205x805x1110", seat: 705, wb: 1485, tank: 12, weight: 181, clearance: 160,
      suspF: "倒置式（行程 130mm）", suspR: "中置单减（行程 96mm）",
      brkF: "φ320mm 单碟 · 四活塞卡钳", brkR: "φ220mm 单碟 · 单活塞卡钳",
      tireF: "130/90-R16", tireR: "150/80-R16",
      abs: "标配前后", tcs: "标配", qs: "无", cruise: "无",
      src: "https://www.58moto.com/good/20571/configuration.html"
    },
    "赛科龙|AQS250": {
      variant: "2026款 AQS250 手动挡", price: "15,999",
      kw: 20.5, kwRpm: 9000, nm: 23.6, nmRpm: 7000, cc: 250, cyl: "双缸 V型",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "皮带传动",
      frame: "高强度钢摇篮式车架",
      lwh: "2230x820x1090", seat: 720, wb: 1460, tank: 16.5, weight: 175, clearance: 170,
      suspF: "倒置式（行程 130mm）", suspR: "边置式双减震（行程 72mm）",
      brkF: "碟刹", brkR: "碟刹",
      tireF: "120/80-16", tireR: "150/80-15",
      abs: "标配前后", tcs: "标配", qs: "无", cruise: "无", tpms: "无",
      keyless: "无", dash: "液晶仪表",
      src: "https://www.58moto.com/good/22728/configuration.html"
    },
    "春风|675NK": {
      variant: "2025款 675NK", price: "35,980",
      kw: 70, kwRpm: 11000, nm: 70, nmRpm: 8250, cc: 675, cyl: "三缸 直列", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钢管车架",
      lwh: "2020x849x1155", seat: 810, wb: 1400, tank: 15, weight: 189, clearance: 140,
      suspF: "KYB 倒置式 φ41mm（内置气囊 · 压缩/回弹可调）",
      suspR: "KYB 中置单减（内置气囊 · 压缩/回弹可调）",
      src: "https://www.58moto.com/good/21533/configuration.html"
    },
    "无极|SR250GT": {
      variant: "2026款 SR250GT Ⅱ代 Play版", price: "15,980",
      kw: 20.5, kwRpm: 8500, nm: 24.5, nmRpm: 6250, cc: 250, cyl: "单缸", cmp: "11.5:1",
      cool: "水冷", gear: "CVT 无级变速", clutch: "干式离心式离合", drive: "皮带传动",
      frame: "钢管编织车架",
      lwh: "2100x795x1390", seat: 770, wb: 1525, tank: 15, weight: 168,
      src: "https://www.58moto.com/good/20509/configuration.html"
    },
    "春风|450NK": {
      variant: "2026款 450NK", price: "23,880",
      kw: 38, kwRpm: 9500, nm: 40, nmRpm: 7750, cc: 450, cyl: "双缸 直列", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钢管编织式车架",
      lwh: "2000x810x1130", seat: 795, wb: 1370, tank: 14, weight: 165,
      suspF: "φ37mm 倒置减震", suspR: "中置单减",
      tireF: "110/70-R17", tireR: "150/60-R17",
      src: "https://www.58moto.com/good/20536/configuration.html"
    },
    "钱江|赛450": {
      variant: "2025款 赛450 AMT版", price: "26,999",
      kw: 39, kwRpm: 9500, nm: 43, nmRpm: 8000, cc: 450, cyl: "双缸 直列", cmp: "11.5:1",
      cool: "水冷", gear: "AMT 6 速自动挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钢管编织车架",
      lwh: "2030x750x1150", seat: 785, wb: 1380, tank: 14.8, weight: 173,
      suspF: "Marzocchi 倒置式前叉", suspR: "中置多连杆 · 预载多段可调",
      brkF: "φ300mm 双碟 · 日清卡钳", brkR: "φ240mm 单碟",
      tireF: "110/70-R17", tireR: "150/60-R17",
      abs: "标配前后", tcs: "标配可关闭", qs: "无", cruise: "无", tpms: "标配",
      dash: "5 寸 TFT 仪表",
      src: "https://www.58moto.com/good/20234/configuration.html"
    },
    "无极|CU525": {
      variant: "2026款 CU525 链条版", price: "21,980",
      kw: 39.6, kwRpm: 8500, nm: 50.5, nmRpm: 7000, cc: 500, cyl: "双缸 直列", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钢管编织车架",
      lwh: "2225x845x1105", seat: 710, wb: 1480, tank: 15, weight: 178, clearance: 160,
      suspF: "φ41mm 倒置减震", suspR: "边置式双减震",
      brkF: "φ310mm 单碟 · 对向四活塞径向卡钳（西互）", brkR: "φ240mm 单碟单活塞（西互）",
      tireF: "130/90-16", tireR: "150/80-16",
      abs: "标配前后", tcs: "标配可关闭", qs: "无", cruise: "无", tpms: "无",
      keyless: "无", dash: "LED 全彩仪表",
      src: "https://www.58moto.com/good/20489/configuration.html"
    },
    "本田|CBR650R": {
      variant: "2024款 CBR650R E-Clutch", price: "82,800",
      kw: 56, kwRpm: 9000, nm: 60, nmRpm: 8000, cc: 650, cyl: "四缸 直列", cmp: "11.6:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合（E-Clutch 电子离合）", drive: "链条传动",
      lwh: "2130x750x1145", seat: 810, wb: 1450, tank: 15.4, weight: 212, clearance: 130,
      suspF: "Showa SFF-BP 倒置式", suspR: "中置单筒",
      brkF: "双 310mm 浮动碟 · 辐射式对向卡钳", brkR: "240mm 单碟 · 单活塞卡钳",
      tireF: "120/70-ZR17", tireR: "180/55-ZR17",
      abs: "标配前后", tcs: "标配可关闭", qs: "无", cruise: "无", tpms: "无",
      keyless: "无", dash: "全数字液晶仪表",
      src: "https://www.58moto.com/good/6938/configuration.html"
    },
    "赛科龙|RT5": {
      variant: "2026款 RT5 智途版", price: "21,988",
      kw: 19.5, kwRpm: 8000, nm: 24.5, nmRpm: 6500, cc: 250, cyl: "单缸", cool: "水冷",
      gear: "CVT 无级变速", clutch: "干式离心式离合", drive: "皮带传动",
      frame: "高强度龙骨车架",
      lwh: "2205x767x1395", seat: 755, wb: 1545, tank: 18, weight: 190, clearance: 155,
      suspF: "正置式前减震", suspR: "弹簧式后减震",
      brkF: "盘式", brkR: "盘式",
      tireF: "120/70-15", tireR: "140/60-14",
      abs: "标配前后",
      src: "https://www.58moto.com/good/21660/configuration.html"
    },
    "升仕|368D": {
      variant: "2026款 368D 全新升级版", price: "28,800",
      kw: 28.5, kwRpm: 7500, nm: 40, nmRpm: 6000, cc: 368, cyl: "单缸", cmp: "11.8:1",
      cool: "水冷+油冷", gear: "CVT 无级变速", clutch: "干式离心式离合", drive: "皮带传动",
      frame: "钢管车架",
      lwh: "2025x805x1190", seat: 760, wb: 1405, tank: 12, weight: 165, clearance: 150,
      suspF: "玛卓科 φ41mm 倒置式（压缩/回弹多段可调）", suspR: "边置式双减震（预载 5 段可调）",
      brkF: "西互对向四活塞辐射式卡钳", brkR: "碟刹",
      tireF: "120/70-15", tireR: "140/70-14",
      abs: "标配前后", tcs: "标配", cruise: "标配", tpms: "标配", keyless: "标配",
      dash: "6.75 寸 TFT 全彩液晶屏",
      src: "https://www.58moto.com/good/21312/configuration.html"
    },
    "赛科龙|AQS401": {
      variant: "2027款 AQS401 AMT版", price: "21,988",
      kw: 34, kwRpm: 9500, nm: 37, nmRpm: 8000, cc: 400, cyl: "双缸 直列",
      cool: "水冷", gear: "AMT 7 速自动挡", clutch: "湿式多片滑动离合", drive: "皮带传动",
      lwh: "2175x845x1145", seat: 720, wb: 1480, tank: 17, weight: 185, clearance: 140,
      suspF: "正置式", suspR: "边置式双减震",
      tireF: "120/80-17", tireR: "150/60-17",
      abs: "标配前后", tcs: "标配", qs: "无", cruise: "无", tpms: "无", keyless: "无",
      dash: "液晶仪表",
      src: "https://www.58moto.com/good/21327/configuration.html"
    },
    "无极|DS525": {
      variant: "2025款 DS525X 公路征途版", price: "31,766",
      kw: 41, kwRpm: 9000, nm: 50.5, nmRpm: 7500, cc: 500, cyl: "双缸 直列", cmp: "11.5:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钢管车架",
      lwh: "2265x940x1360", seat: 810, wb: 1450, tank: 18, weight: 216, clearance: 200,
      src: "https://www.58moto.com/good/20040/configuration.html"
    },
    "凯越|800X": {
      variant: "2026款 800X 硬汉", price: "42,800",
      kw: 71, kwRpm: 9000, nm: 80, nmRpm: 7500, cc: 800, cyl: "双缸 直列", cmp: "13:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      frame: "钻石双翼梁一体式车架",
      lwh: "2270x940x1380", seat: 875, wb: 1540, tank: 20, weight: 194, clearance: 265,
      suspF: "KYB 倒置式 φ48mm · 行程 240mm（预载/压缩/回弹可调）",
      suspR: "KYB 中置多连杆 · 行程 230mm（预载/压缩/回弹可调）",
      brkF: "双浮动碟 · 对置四活塞卡钳（泰斯克）", brkR: "单碟 · 单活塞卡钳（泰斯克）",
      tireF: "90/90-21", tireR: "150/70-R18",
      abs: "标配前后（可关闭）", tcs: "标配", qs: "标配双向", cruise: "标配", tpms: "标配",
      dash: "竖屏 TFT 仪表",
      src: "https://www.58moto.com/good/19587/configuration.html"
    },
    "本田|CB650R": {
      variant: "2024款 CB650R E-Clutch", price: "76,800",
      kw: 56, kwRpm: 9000, nm: 60, nmRpm: 9000, cc: 650, cyl: "四缸 直列", cmp: "11.6:1",
      cool: "水冷", gear: "国际6挡", clutch: "湿式多片滑动离合（E-Clutch 电子离合）", drive: "链条传动",
      lwh: "2130x780x1075", seat: 810, wb: 1450, tank: 15.4, weight: 207, clearance: 150,
      suspF: "Showa SFF-BP 倒置式", suspR: "中置单筒",
      brkF: "液压双碟", brkR: "液压单碟",
      tireF: "120/70-ZR17", tireR: "180/55-ZR17",
      abs: "标配前后", tcs: "标配", qs: "无", cruise: "无", tpms: "无", keyless: "无",
      dash: "液晶显示屏",
      src: "https://www.58moto.com/good/6541/configuration.html"
    },
    "本田|NC750X": {
      variant: "2025款 NC750X DCT", price: "91,800",
      kw: 43.1, kwRpm: 6750, nm: 69, nmRpm: 4750, cc: 750, cyl: "双缸 直列", cmp: "10.7:1",
      cool: "水冷", gear: "DCT 6 速自动挡", clutch: "湿式多片离合", drive: "链条传动",
      lwh: "2210x846x1330", seat: 802, wb: 1530, tank: 14.1, weight: 226, clearance: 145,
      suspF: "41mm 伸缩式前叉",
      brkF: "双碟刹", brkR: "240mm 单碟",
      tireF: "120/70-ZR17", tireR: "160/60-ZR17",
      src: "https://www.58moto.com/good/5556/configuration.html"
    },
    "本田|CB750": {
      variant: "2023款 CB750 Hornet", price: "68,800",
      kw: 51, nm: 69, cc: 750, cyl: "双缸 直列", cool: "水冷",
      gear: "国际6挡", clutch: "湿式多片滑动离合", drive: "链条传动",
      lwh: "2090x780x1085", seat: 795, wb: 1420, tank: 15.2, weight: 190, clearance: 140,
      suspF: "SFF-BP 倒立式前叉", suspR: "单减震 · Pro-Link 多连杆摇臂",
      brkF: "双碟刹", brkR: "单碟刹",
      tireF: "120/70-17", tireR: "160/60-17",
      abs: "标配前后", tcs: "标配", qs: "无", cruise: "无", tpms: "无", keyless: "无",
      dash: "5 英寸 TFT 全彩液晶仪表",
      src: "https://www.58moto.com/good/20569/configuration.html"
    }
  }
};
