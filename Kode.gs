const _K = _s([75,48]);
const _C = _s([67,95]);

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) return _r({ok:true});
    const b = JSON.parse(e.postData.contents);
    const p = PropertiesService.getScriptProperties();
    const secret = p.getProperty(_K);

    if (!secret || String(b.secret || "") !== String(secret)) {
      return _r({ok:false,error:"Unauthorized"});
    }

    const out = _x(String(b.action || "").trim(), b.data || {});
    return _r({ok:true,data:out});
  } catch (err) {
    console.error(String(err && err.message || err));
    return _r({
      ok:false,
      error:String(err && err.message || err)
    });
  }
}

function _x(a, d) {
  const p = PropertiesService.getScriptProperties();
  const secret = p.getProperty(_K);

  if (!secret) throw new Error("Runtime unavailable.");

  const h = _h(a, secret);

  const r0 = p.getProperty(_s([82,48])) || "";
  const r1 = p.getProperty(_s([82,49])) || "";
  const r2 = p.getProperty(_s([82,50])) || "";
  const r3 = p.getProperty(_s([82,51])) || "";
  const r4 = p.getProperty(_s([82,52])) || "";

  if (h === r0) return _a(d);
  if (h === r1) return _b(d);
  if (h === r2) return _c(d);
  if (h === r3) return _d(d);
  if (h === r4) return _e(d);

  throw new Error("Invalid operation");
}

function _a(d) {
  const rows = _q(1).getDataRange().getDisplayValues();
  const out = [];

  for (let i = 1; i < rows.length; i++) {
    const name = _n(rows[i][0]);
    const user = String(rows[i][1] || "").trim();
    const chat = String(rows[i][2] || "").trim();
    const st = String(rows[i][3] || "").trim().toUpperCase();

    if (st === _s([79,78,76,73,78,69]) && chat) {
      out.push({
        name:name,
        username:user,
        chat_id:chat,
        status:st
      });
    }
  }

  return {items:out};
}

function _b(d) {
  const key = String(
    d[_s([107,101,121])] || ""
  ).trim();

  const step = Number(
    d[_s([115,116,101,112])] || 1
  );

  if (!key) {
    throw new Error("Invalid counter key.");
  }

  if (!Number.isFinite(step) || step === 0) {
    throw new Error("Invalid counter step.");
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);

  try {
    const props = PropertiesService.getScriptProperties();
    const propName = _C + key;
    const current = Number(
      props.getProperty(propName) || 0
    );
    const next = current + step;

    props.setProperty(
      propName,
      String(next)
    );

    return {
      value:current,
      next:next
    };
  } finally {
    lock.releaseLock();
  }
}

function _c(d) {
  const sh = _q(0);
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);

  try {
    const rows = sh.getDataRange().getDisplayValues();
    const inner = d[_s([100,97,116,97])] || {};

    const noOrder = String(
      inner[_s([110,111,95,111,114,100,101,114])] || ""
    ).trim();

    if (!noOrder) {
      throw new Error("Invalid payload.");
    }

    for (let i = 1; i < rows.length; i++) {
      const existing = String(
        rows[i][4] || ""
      ).trim();

      const status = String(
        rows[i][15] || ""
      ).trim().toUpperCase();

      if (
        existing === noOrder &&
        status !== _s([83,69,76,69,83,65,73])
      ) {
        return {duplicate:true};
      }
    }

    const username = String(
      d[_s([117,115,101,114,110,97,109,101])] || ""
    ).trim();

    const sender = String(
      d[_s([115,101,110,100,101,114])] || "User"
    );

    const waktu = Utilities.formatDate(
      new Date(),
      "Asia/Jakarta",
      "yyyy-MM-dd HH:mm:ss"
    );

    const hdAssigned = String(
      d[_s([104,100,65,115,115,105,103,110,101,100])] ||
      "Belum Diassign"
    );

    const chatId = String(
      d[_s([99,104,97,116,73,100])] || ""
    );

    const messageId = String(
      d[_s([109,101,115,115,97,103,101,73,100])] || ""
    );

    const jenis = String(
      inner[_s([106,101,110,105,115])] || "-"
    );

    const sto = String(
      inner[_s([115,116,111])] || "-"
    );

    const noInternet = String(
      inner[_s([
        110,111,95,105,110,116,101,114,110,101,116
      ])] || "-"
    );

    const snModem = String(
      inner[_s([
        115,110,95,109,111,100,101,109
      ])] || "-"
    );

    const odp = String(
      inner[_s([111,100,112])] || "-"
    );

    const port = String(
      inner[_s([112,111,114,116])] || "-"
    );

    const barcode = String(
      inner[_s([98,97,114,99,111,100,101])] || "-"
    );

    const idValin = String(
      inner[_s([
        105,100,95,118,97,108,105,110
      ])] || "-"
    );

    const wonum = String(
      inner[_s([119,111,110,117,109])] || "-"
    );

    const fallout = String(
      inner[_s([
        116,105,107,101,116,95,102,97,108,108,111,117,116
      ])] || "-"
    );

    const ket = String(
      inner[_s([
        107,101,116,101,114,97,110,103,97,110
      ])] || "-"
    );

    sh.appendRow([
      waktu,
      sender,
      username === "TanpaUsername"
        ? "TanpaUsername"
        : "@" + username.replace(/^@/, ""),
      jenis,
      noOrder,
      sto,
      noInternet,
      snModem,
      odp,
      port,
      barcode,
      idValin,
      wonum,
      fallout,
      ket,
      _s([66,69,76,85,77,32,83,69,76,69,83,65,73]),
      hdAssigned,
      "'" + chatId,
      "'" + messageId
    ]);

    return {duplicate:false};
  } finally {
    lock.releaseLock();
  }
}

function _d(d) {
  const sh = _q(0);
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);

  try {
    const rows = sh.getDataRange().getDisplayValues();

    const target = String(
      d[_s([110,111,79,114,100,101,114])] || ""
    ).trim();

    const actorChatId = String(
      d[_s([99,104,97,116,73,100])] || ""
    ).trim();

    const actorUsername = String(
      d[_s([117,115,101,114,110,97,109,101])] || ""
    )
      .trim()
      .replace(/^@/, "")
      .toLowerCase();

    for (let i = rows.length - 1; i >= 1; i--) {
      const noOrder = String(
        rows[i][4] || ""
      ).trim();

      if (noOrder !== target) continue;

      const status = String(
        rows[i][15] || ""
      ).trim().toUpperCase();

      const assignedHD = String(
        rows[i][16] || ""
      ).trim();

      const asalChatId = String(
        rows[i][17] || ""
      ).replace(/['\s]/g, "");

      const asalMessageId = String(
        rows[i][18] || ""
      ).replace(/['\s]/g, "");

      if (
        status === _s([
          83,69,76,69,83,65,73
        ])
      ) {
        return {
          found:true,
          alreadyDone:true,
          assignedHD:assignedHD,
          asalChatId:asalChatId,
          asalMessageId:asalMessageId
        };
      }

      const bypass = Boolean(
        d[_s([
          98,121,112,97,115,115,
          65,115,115,105,103,110,
          109,101,110,116
        ])]
      );

      if (
        !bypass &&
        !_f(
          assignedHD,
          actorChatId,
          actorUsername
        )
      ) {
        return {
          found:true,
          alreadyDone:false,
          forbidden:true,
          assignedHD:assignedHD,
          asalChatId:asalChatId,
          asalMessageId:asalMessageId
        };
      }

      const keterangan = String(
        d[_s([
          107,101,116,101,114,97,110,103,97,110
        ])] || "-"
      );

      const sender = String(
        d[_s([
          115,101,110,100,101,114
        ])] || "User"
      );

      sh.getRange(
        i + 1,
        15
      ).setValue(keterangan);

      sh.getRange(
        i + 1,
        16
      ).setValue(
        _s([83,69,76,69,83,65,73])
      );

      sh.getRange(
        i + 1,
        17
      ).setValue(sender);

      return {
        found:true,
        alreadyDone:false,
        forbidden:false,
        assignedHD:assignedHD,
        asalChatId:asalChatId,
        asalMessageId:asalMessageId
      };
    }

    return {found:false};
  } finally {
    lock.releaseLock();
  }
}

function _e(d) {
  const sh = _q(1);
  const rows = sh.getDataRange().getDisplayValues();

  const target = String(
    d[_s([99,104,97,116,73,100])] || ""
  ).trim();

  const status = String(
    d[_s([115,116,97,116,117,115])] || ""
  ).trim().toUpperCase();

  const sender = String(
    d[_s([115,101,110,100,101,114])] || "User"
  );

  const username = String(
    d[_s([117,115,101,114,110,97,109,101])] || ""
  ).trim();

  if (
    [
      _s([79,78,76,73,78,69]),
      _s([79,70,70,76,73,78,69]),
      _s([66,82,69,65,75])
    ].includes(status) === false
  ) {
    throw new Error("Invalid value.");
  }

  for (let i = 1; i < rows.length; i++) {
    if (
      String(rows[i][2] || "").trim() === target
    ) {
      sh.getRange(
        i + 1,
        1
      ).setValue(sender);

      sh.getRange(
        i + 1,
        4
      ).setValue(status);

      return {updated:true};
    }
  }

  sh.appendRow([
    sender,
    username === "TanpaUsername"
      ? "TanpaUsername"
      : "@" + username.replace(/^@/, ""),
    target,
    status
  ]);

  return {updated:true};
}

function _f(name, chatId, username) {
  if (!name) return false;

  const rows = _q(1)
    .getDataRange()
    .getDisplayValues();

  for (let i = 1; i < rows.length; i++) {
    const n = _n(rows[i][0]);

    const u = String(
      rows[i][1] || ""
    )
      .trim()
      .replace(/^@/, "")
      .toLowerCase();

    const c = String(
      rows[i][2] || ""
    ).trim();

    if (
      n === name &&
      (c === chatId || u === username)
    ) {
      return true;
    }
  }

  return false;
}

function _q(slot) {
  const p = PropertiesService.getScriptProperties();

  const key =
    slot === 0
      ? _s([83,48])
      : _s([83,49]);

  const name = p.getProperty(key);

  if (!name) {
    throw new Error("Storage unavailable.");
  }

  const ss =
    SpreadsheetApp.getActiveSpreadsheet();

  const sh =
    ss.getSheetByName(name);

  if (!sh) {
    throw new Error("Storage unavailable.");
  }

  return sh;
}

function _n(v) {
  if (!v) return "User";

  return String(v)
    .replace(
      new RegExp(
        _s([
          94,40,115,97,109,97,114,105,110,100,97,
          124,115,109,100,124,116,101,108,107,111,109,
          124,119,111,99,124,104,100,41,
          92,115,42,91,45,58,93,92,115,42
        ]),
        "i"
      ),
      ""
    )
    .trim();
}

function _s(a) {
  return String.fromCharCode.apply(null, a);
}

function _h(v, k) {
  const bytes =
    Utilities.computeHmacSha256Signature(
      String(v),
      String(k),
      Utilities.Charset.UTF_8
    );

  return bytes
    .map(function(b) {
      const n =
        b < 0 ? b + 256 : b;

      return (
        "0" +
        n.toString(16)
      ).slice(-2);
    })
    .join("");
}

function _r(obj) {
  return ContentService
    .createTextOutput(
      JSON.stringify(obj)
    )
    .setMimeType(
      ContentService.MimeType.JSON
    );
}