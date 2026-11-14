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
    }
  }
};
