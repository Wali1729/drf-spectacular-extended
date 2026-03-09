"use strict";

const DSE_VERSIONS_URL = "{{ versions_url|escapejs }}";
const DSE_SCHEMA_URL = "{{ schema_url|escapejs }}";
const DSE_CURRENT_VERSION = "{{ current_doc_version|escapejs }}";

let dseVersionsCache = null;

function dseSwitch(tab) {
  document.querySelectorAll(".dse-tab-bar button").forEach(function(btn) {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  document.querySelectorAll(".dse-tab-content").forEach(function(el) {
    el.classList.toggle("active", el.id === "tab-" + tab);
  });
  if (tab === "changes") { dseLoadChanges(); }
  if (tab === "releases") { dseLoadReleases(); }
}

function dseVersionChange(version) {
  if (!version) return;
  var sep = DSE_SCHEMA_URL.indexOf("?") === -1 ? "?" : "&";
  var newUrl = DSE_SCHEMA_URL + sep + "doc_version=" + encodeURIComponent(version);
  ui.specActions.updateUrl(newUrl);
  ui.specActions.download();
  dseLoadChangesForVersion(version);
}

function dseFetchVersions(callback) {
  if (dseVersionsCache) { callback(dseVersionsCache); return; }
  if (!DSE_VERSIONS_URL) { callback([]); return; }
  fetch(DSE_VERSIONS_URL)
    .then(function(r) { return r.json(); })
    .then(function(data) { dseVersionsCache = data; callback(data); })
    .catch(function() { callback([]); });
}

function dsePopulateSelector() {
  dseFetchVersions(function(versions) {
    var sel = document.getElementById("dse-version-selector");
    if (!sel) return;
    sel.innerHTML = "";
    if (versions.length === 0) {
      sel.innerHTML = '<option value="">No versions</option>';
      return;
    }
    versions.forEach(function(v) {
      var opt = document.createElement("option");
      opt.value = v.version;
      opt.textContent = v.version;
      if (v.version === DSE_CURRENT_VERSION) { opt.selected = true; }
      sel.appendChild(opt);
    });
  });
}

function dseRenderBadges(items, cssClass) {
  if (!items || items.length === 0) return '<span class="dse-empty">None</span>';
  return items.map(function(ep) {
    return '<span class="dse-badge ' + cssClass + '">' + dseEscape(ep) + '</span>';
  }).join(" ");
}

function dseEscape(s) {
  var d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function dseLoadChanges() {
  var sel = document.getElementById("dse-version-selector");
  var ver = sel ? sel.value : DSE_CURRENT_VERSION;
  dseLoadChangesForVersion(ver);
}

function dseLoadChangesForVersion(version) {
  dseFetchVersions(function(versions) {
    var panel = document.getElementById("dse-changes-panel");
    var match = versions.find(function(v) { return v.version === version; });
    if (!match || !match.changes_summary) {
      panel.innerHTML = '<h2>Changes for ' + dseEscape(version) + '</h2>' +
        '<p class="dse-empty">No change data available for this version.</p>';
      return;
    }
    var cs = match.changes_summary;
    panel.innerHTML = '<h2>Changes for ' + dseEscape(version) + '</h2>' +
      '<div class="dse-section"><h3>New Endpoints (' + (cs.new ? cs.new.length : 0) + ')</h3>' +
      dseRenderBadges(cs.new, "dse-badge-new") + '</div>' +
      '<div class="dse-section"><h3>Modified Endpoints (' + (cs.modified ? cs.modified.length : 0) + ')</h3>' +
      dseRenderBadges(cs.modified, "dse-badge-modified") + '</div>' +
      '<div class="dse-section"><h3>Removed Endpoints (' + (cs.removed ? cs.removed.length : 0) + ')</h3>' +
      dseRenderBadges(cs.removed, "dse-badge-removed") + '</div>';
  });
}

function dseLoadReleases() {
  dseFetchVersions(function(versions) {
    var panel = document.getElementById("dse-releases-panel");
    if (versions.length === 0) {
      panel.innerHTML = '<h2>Releases</h2><p class="dse-empty">No releases found.</p>';
      return;
    }
    var rows = versions.map(function(v) {
      var cs = v.changes_summary || {};
      var nNew = cs.new ? cs.new.length : 0;
      var nMod = cs.modified ? cs.modified.length : 0;
      var nRem = cs.removed ? cs.removed.length : 0;
      var date = v.created_at ? new Date(v.created_at).toLocaleDateString(undefined, {
        year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
      }) : "—";
      return '<tr>' +
        '<td><a class="dse-version-link" onclick="dseSelectRelease(\'' + dseEscape(v.version) + '\')">' +
        dseEscape(v.version) + '</a></td>' +
        '<td>' + date + '</td>' +
        '<td><span class="dse-count dse-count-new">' + nNew + ' new</span></td>' +
        '<td><span class="dse-count dse-count-mod">' + nMod + ' modified</span></td>' +
        '<td><span class="dse-count dse-count-rem">' + nRem + ' removed</span></td>' +
        '</tr>';
    }).join("");
    panel.innerHTML = '<h2>Releases</h2>' +
      '<table class="dse-release-table"><thead><tr>' +
      '<th>Version</th><th>Date</th><th>New</th><th>Modified</th><th>Removed</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>';
  });
}

function dseSelectRelease(version) {
  var sel = document.getElementById("dse-version-selector");
  if (sel) { sel.value = version; }
  dseVersionChange(version);
  dseSwitch("docs");
}

dsePopulateSelector();
