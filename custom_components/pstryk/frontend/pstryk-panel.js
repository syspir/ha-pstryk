// Marcin Koźliński
// Ostatnia modyfikacja: 2026-04-11

function _getLitElement() {
  const candidates = ["hui-view", "ha-panel-lovelace", "home-assistant", "hc-lovelace"];
  for (const name of candidates) {
    const el = customElements.get(name);
    if (el) {
      const proto = Object.getPrototypeOf(el);
      if (proto && proto.prototype && proto.prototype.html) return proto;
    }
  }
  return null;
}

async function _waitForLitElement() {
  const lit = _getLitElement();
  if (lit) return lit;
  return new Promise((resolve) => {
    const check = () => {
      const lit = _getLitElement();
      if (lit) { resolve(lit); return; }
      setTimeout(check, 100);
    };
    setTimeout(check, 100);
  });
}

const LitElement = _getLitElement() || await _waitForLitElement();

const html = LitElement.prototype.html;

const css = LitElement.prototype.css || function(strings, ...values) {
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(strings.reduce((acc, str, i) => acc + str + (values[i] ?? ""), ""));
  return sheet;
};

class PstrykPanel extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      panel: { type: Object },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        padding: 16px;
        max-width: 1200px;
        margin: 0 auto;
        --pstryk-green: #4caf50;
        --pstryk-red: #f44336;
        --pstryk-orange: #ff9800;
        --pstryk-blue: #2196f3;
      }
      .header {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 24px;
        font-weight: 400;
        color: var(--primary-text-color);
        padding: 8px 0 16px;
      }
      .header-logos {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-left: auto;
      }
      .header-logo {
        opacity: 0.6;
        transition: opacity 0.2s;
      }
      .header-logo:hover {
        opacity: 1;
      }
      .header-logo img {
        height: 28px;
        vertical-align: middle;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      .grid-full {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
        margin-bottom: 16px;
      }
      ha-card {
        padding: 16px;
        box-sizing: border-box;
      }
      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        font-weight: 500;
        color: var(--primary-text-color);
        padding-bottom: 12px;
        border-bottom: 1px solid var(--divider-color);
        margin-bottom: 8px;
      }
      .card-header ha-icon {
        color: var(--primary-color);
        --mdc-icon-size: 20px;
      }
      .metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.08));
      }
      .metric:last-child {
        border-bottom: none;
      }
      .metric-label {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      .metric-label ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }
      .metric-value {
        font-weight: 500;
        color: var(--primary-text-color);
        font-size: 14px;
        text-align: right;
      }
      .metric-unit {
        color: var(--secondary-text-color);
        font-size: 12px;
        margin-left: 4px;
      }
      .live-card {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
      .live-card .card-header {
        color: var(--text-primary-color);
        border-bottom-color: rgba(255,255,255,0.3);
      }
      .live-card .card-header ha-icon {
        color: var(--text-primary-color);
      }
      .live-card .metric-label,
      .live-card .metric-unit {
        color: rgba(255,255,255,0.8);
      }
      .live-card .metric-label ha-icon {
        color: rgba(255,255,255,0.8);
      }
      .live-card .metric-value {
        color: var(--text-primary-color);
        font-size: 16px;
      }
      .live-card .metric {
        border-bottom-color: rgba(255,255,255,0.15);
      }
      .live-price-main {
        text-align: center;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255,255,255,0.15);
      }
      .live-price-value {
        font-size: 36px;
        font-weight: 700;
      }
      .live-price-unit {
        font-size: 14px;
        opacity: 0.8;
        margin-left: 4px;
      }
      .live-price-label {
        font-size: 12px;
        opacity: 0.7;
        margin-top: 4px;
      }
      .live-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0 24px;
      }
      .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        color: white;
        margin-left: auto;
      }
      .badge-cheap {
        background: var(--pstryk-green);
      }
      .badge-expensive {
        background: var(--pstryk-red);
      }
      .badge-neutral {
        background: rgba(255,255,255,0.3);
      }
      .section-title {
        font-size: 14px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--secondary-text-color);
        margin: 24px 0 8px;
      }
      .section-title:first-of-type {
        margin-top: 8px;
      }
      .price-time {
        font-size: 11px;
        color: var(--secondary-text-color);
        margin-top: 2px;
      }
      .empty-message {
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text-color);
        font-size: 14px;
      }
      .chart-container {
        position: relative;
        display: flex;
        gap: 4px;
        padding: 8px 12px;
      }
      .chart-price-labels {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-size: 11px;
        color: var(--secondary-text-color);
        padding: 0 4px 36px 0;
        text-align: right;
        min-width: 36px;
      }
      .chart-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
      }
      .chart-bars {
        position: relative;
        display: flex;
        height: 180px;
        gap: 1px;
      }
      .chart-grid {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        pointer-events: none;
        padding: 0 0 36px 0;
        z-index: 0;
      }
      .chart-grid-line {
        border-top: 1px solid var(--divider-color, #e0e0e0);
      }
      .chart-grid-line--dashed {
        border-top-style: dashed;
      }
      .chart-bar-col {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        min-width: 0;
        position: relative;
        z-index: 1;
      }
      .chart-bar-col--sep {
        margin-left: 3px;
        border-left: 1px dashed var(--secondary-text-color, #999);
        padding-left: 2px;
      }
      .chart-bar {
        width: 100%;
        border-radius: 2px 2px 0 0;
        transition: height 0.3s ease;
        min-height: 2px;
      }
      .chart-bar--normal { background: var(--pstryk-blue); }
      .chart-bar--cheap { background: var(--pstryk-green); }
      .chart-bar--expensive { background: var(--pstryk-red); }
      .chart-bar--current { background: var(--primary-color); }
      .chart-bar--highlight {
        box-shadow: 0 0 0 2px var(--primary-text-color);
      }
      .chart-hour-labels {
        display: flex;
        gap: 1px;
      }
      .chart-hour-label {
        flex: 1;
        text-align: center;
        font-size: 10px;
        color: var(--secondary-text-color);
        padding-top: 4px;
        min-width: 0;
        overflow: hidden;
      }
      .chart-day-labels {
        display: flex;
      }
      .chart-day-label {
        text-align: center;
        font-size: 11px;
        font-weight: 500;
        color: var(--secondary-text-color);
        padding-top: 2px;
      }
      .chart-legend {
        display: flex;
        gap: 16px;
        justify-content: center;
        padding: 8px 0 0;
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .chart-legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .chart-legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 2px;
      }
      @media (max-width: 600px) {
        :host { padding: 8px; }
        .grid { grid-template-columns: 1fr; }
        .live-grid { grid-template-columns: 1fr; }
        .chart-bars { height: 140px; }
      }
    `;
  }

  _getState(entityId) {
    const state = this.hass?.states[entityId];
    if (!state || state.state === "unavailable" || state.state === "unknown") {
      return null;
    }
    return state.state;
  }

  _getUnit(entityId) {
    return this.hass?.states[entityId]?.attributes?.unit_of_measurement || "";
  }

  _getAttr(entityId, attr) {
    return this.hass?.states[entityId]?.attributes?.[attr];
  }

  _formatPrice(val) {
    if (val === null || val === undefined) return "---";
    return `${Number(val).toFixed(2)}`;
  }

  _formatPriceUnit(val, unit) {
    if (val === null || val === undefined) return "---";
    return `${Number(val).toFixed(2)} ${unit || "PLN/kWh"}`;
  }

  _formatTime(isoString) {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  }

  _entityExists(entityId) {
    return !!this.hass?.states[entityId];
  }

  _renderMetricIcon(icon, label, entityId) {
    const val = this._getState(entityId);
    const unit = this._getUnit(entityId);
    return html`
      <div class="metric">
        <span class="metric-label">
          <ha-icon icon="${icon}"></ha-icon>
          ${label}
        </span>
        <span class="metric-value">
          ${val !== null ? val : "---"}
          ${val !== null && unit ? html`<span class="metric-unit">${unit}</span>` : ""}
        </span>
      </div>
    `;
  }

  _renderAttrMetric(icon, label, value, unit) {
    return html`
      <div class="metric">
        <span class="metric-label">
          <ha-icon icon="${icon}"></ha-icon>
          ${label}
        </span>
        <span class="metric-value">
          ${this._formatPrice(value)}
          ${value !== null && value !== undefined ? html`<span class="metric-unit">${unit || "PLN/kWh"}</span>` : ""}
        </span>
      </div>
    `;
  }

  _renderLiveSection() {
    const prefix = "sensor.pstryk_energy_";
    const priceEntity = `${prefix}cena_energii_zakup_brutto`;
    const fullPrice = this._getState(priceEntity);
    const unit = this._getUnit(priceEntity);
    const isCheap = this._getAttr(priceEntity, "is_cheap");
    const isExpensive = this._getAttr(priceEntity, "is_expensive");

    let badge = html``;
    if (isCheap === true || isCheap === "True") {
      badge = html`<span class="badge badge-cheap">Tania</span>`;
    } else if (isExpensive === true || isExpensive === "True") {
      badge = html`<span class="badge badge-expensive">Droga</span>`;
    } else if (isCheap !== null && isCheap !== undefined) {
      badge = html`<span class="badge badge-neutral">Normalna</span>`;
    }

    const prosumerEntity = `${prefix}cena_sprzedazy_energii_brutto`;
    const hasProsumer = this._entityExists(prosumerEntity);

    return html`
      <div class="section-title">Bieżąca godzina</div>
      <div class="grid-full">
        <ha-card class="live-card">
          <div class="card-header">
            <ha-icon icon="mdi:pulse"></ha-icon>
            Dane na żywo
            ${badge}
          </div>
          <div class="live-price-main">
            <div>
              <span class="live-price-value">${fullPrice !== null ? fullPrice : "---"}</span>
              <span class="live-price-unit">${unit}</span>
            </div>
            <div class="live-price-label">Cena zakupu brutto (z dystrybucją)</div>
          </div>
          <div class="live-grid">
            ${this._renderAttrMetric("mdi:lightning-bolt", "Cena TGE", this._getAttr(priceEntity, "base_price"), "PLN/kWh")}
            ${this._renderAttrMetric("mdi:transmission-tower", "Dystrybucja", this._getAttr(priceEntity, "dist_price"), "PLN/kWh")}
            ${this._renderAttrMetric("mdi:cog", "Opłata serwisowa", this._getAttr(priceEntity, "service_price"), "PLN/kWh")}
            ${this._renderAttrMetric("mdi:gavel", "Akcyza", this._getAttr(priceEntity, "excise_component"), "PLN/kWh")}
            ${this._renderAttrMetric("mdi:percent-outline", "VAT", this._getAttr(priceEntity, "vat_component"), "PLN/kWh")}
            ${hasProsumer ? this._renderMetricIcon("mdi:solar-power-variant", "Cena sprzedaży", prosumerEntity) : ""}
            ${this._renderMetricIcon("mdi:flash", "Pobrana", `${prefix}energia_pobrana_biezaca_godzina`)}
            ${this._renderMetricIcon("mdi:flash-outline", "Oddana", `${prefix}energia_oddana_biezaca_godzina`)}
            ${this._renderMetricIcon("mdi:cash-clock", "Koszt", `${prefix}koszt_biezaca_godzina`)}
          </div>
        </ha-card>
      </div>
    `;
  }

  _renderEnergySection() {
    const prefix = "sensor.pstryk_energy_";
    return html`
      <div class="section-title">Energia</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:calendar-today"></ha-icon>
            Dziś
          </div>
          ${this._renderMetricIcon("mdi:transmission-tower-import", "Pobrana", `${prefix}energia_pobrana_dzis`)}
          ${this._renderMetricIcon("mdi:transmission-tower-export", "Oddana", `${prefix}energia_oddana_dzis`)}
          ${this._renderMetricIcon("mdi:scale-balance", "Bilans", `${prefix}bilans_energii_dzis`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:calendar-month"></ha-icon>
            Miesiąc
          </div>
          ${this._renderMetricIcon("mdi:transmission-tower-import", "Pobrana", `${prefix}energia_pobrana_w_miesiacu`)}
          ${this._renderMetricIcon("mdi:transmission-tower-export", "Oddana", `${prefix}energia_oddana_w_miesiacu`)}
          ${this._renderMetricIcon("mdi:scale-balance", "Bilans", `${prefix}bilans_energii_w_miesiacu`)}
        </ha-card>
      </div>
    `;
  }

  _renderCostSection() {
    const prefix = "sensor.pstryk_energy_";
    return html`
      <div class="section-title">Koszty</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:cash"></ha-icon>
            Dziś
          </div>
          ${this._renderMetricIcon("mdi:cash-minus", "Koszt energii", `${prefix}koszt_energii_dzis`)}
          ${this._renderMetricIcon("mdi:cash-plus", "Wartość sprzedanej", `${prefix}wartosc_sprzedanej_energii_dzis`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:cash-multiple"></ha-icon>
            Miesiąc
          </div>
          ${this._renderMetricIcon("mdi:cash-minus", "Koszt energii", `${prefix}koszt_energii_w_miesiacu`)}
          ${this._renderMetricIcon("mdi:cash-plus", "Wartość sprzedanej", `${prefix}wartosc_sprzedanej_energii_w_miesiacu`)}
        </ha-card>
      </div>
    `;
  }

  _renderPriceChart() {
    const prefix = "sensor.pstryk_energy_";
    const priceEntity = `${prefix}cena_energii_zakup_brutto`;
    const forecast = this._getAttr(priceEntity, "price_forecast");

    if (!forecast || !forecast.length) {
      return html`
        <div class="section-title">Prognoza cen</div>
        <div class="grid-full">
          <ha-card>
            <div class="card-header">
              <ha-icon icon="mdi:chart-bar"></ha-icon>
              Ceny godzinowe (zakup brutto)
            </div>
            <div class="empty-message">Brak danych o prognozach cen</div>
          </ha-card>
        </div>
      `;
    }

    // Group frames by day
    const now = new Date();
    const todayStr = now.toLocaleDateString("pl-PL");
    const frames = forecast
      .filter(f => f.start && ((f.full_price != null && f.full_price > 0) || (f.price_gross != null && f.price_gross > 0)))
      .map(f => {
        const d = new Date(f.start);
        return {
          hour: d.getHours(),
          date: d,
          dateStr: d.toLocaleDateString("pl-PL"),
          price: f.full_price != null ? f.full_price : f.price_gross,
          isCheap: f.is_cheap,
          isExpensive: f.is_expensive,
          isCurrent: d.getHours() === now.getHours() && d.toDateString() === now.toDateString(),
        };
      });

    if (!frames.length) {
      return html`
        <div class="section-title">Prognoza cen</div>
        <div class="grid-full">
          <ha-card>
            <div class="card-header">
              <ha-icon icon="mdi:chart-bar"></ha-icon>
              Ceny godzinowe (zakup brutto)
            </div>
            <div class="empty-message">Brak danych o prognozach cen</div>
          </ha-card>
        </div>
      `;
    }

    const prices = frames.map(f => f.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 0.01;

    const barCount = frames.length;

    // Find day boundaries
    const days = [];
    let lastDateStr = "";
    frames.forEach((f, i) => {
      if (f.dateStr !== lastDateStr) {
        days.push({ index: i, dateStr: f.dateStr, date: f.date });
        lastDateStr = f.dateStr;
      }
    });

    const dayNames = ["Niedz.", "Pon.", "Wt.", "Śr.", "Czw.", "Pt.", "Sob."];

    // Hour labels interval
    const labelInterval = barCount > 30 ? 6 : 3;

    // Price labels
    const priceLabelMin = minPrice.toFixed(2);
    const priceLabelMax = maxPrice.toFixed(2);
    const priceLabelMid = ((minPrice + maxPrice) / 2).toFixed(2);

    return html`
      <div class="section-title">Prognoza cen</div>
      <div class="grid-full">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:chart-bar"></ha-icon>
            Ceny godzinowe (zakup brutto)
          </div>
          <div class="chart-container">
            <div class="chart-price-labels">
              <span>${priceLabelMax}</span>
              <span>${priceLabelMid}</span>
              <span>${priceLabelMin}</span>
            </div>
            <div class="chart-body">
              <div class="chart-grid">
                <div class="chart-grid-line"></div>
                <div class="chart-grid-line chart-grid-line--dashed"></div>
                <div class="chart-grid-line chart-grid-line--dashed"></div>
              </div>
              <div class="chart-bars">
                ${frames.map((f, i) => {
                  const pct = ((f.price - minPrice) / priceRange) * 100;
                  const barPct = Math.max(1.5, pct);
                  let colorClass = "chart-bar--normal";
                  if (f.isCurrent) colorClass = "chart-bar--current";
                  else if (f.isCheap === true || f.isCheap === "True") colorClass = "chart-bar--cheap";
                  else if (f.isExpensive === true || f.isExpensive === "True") colorClass = "chart-bar--expensive";
                  const isDaySep = i > 0 && f.dateStr !== frames[i - 1].dateStr;
                  return html`
                    <div class="chart-bar-col ${isDaySep ? 'chart-bar-col--sep' : ''}"
                         title="${f.hour}:00 — ${f.price.toFixed(4)} PLN/kWh">
                      <div class="chart-bar ${colorClass} ${f.isCurrent ? 'chart-bar--highlight' : ''}"
                           style="height: ${barPct}%"></div>
                    </div>
                  `;
                })}
              </div>
              <div class="chart-hour-labels">
                ${frames.map((f, i) => html`
                  <div class="chart-hour-label">
                    ${f.hour % labelInterval === 0 ? String(f.hour).padStart(2, "0") : ""}
                  </div>
                `)}
              </div>
              <div class="chart-day-labels">
                ${days.map((d, di) => {
                  const nextIdx = di + 1 < days.length ? days[di + 1].index : frames.length;
                  const span = nextIdx - d.index;
                  const dayName = d.date.toDateString() === now.toDateString()
                    ? "Dziś"
                    : d.date.toDateString() === new Date(now.getTime() + 86400000).toDateString()
                      ? "Jutro"
                      : dayNames[d.date.getDay()];
                  return html`
                    <div class="chart-day-label" style="flex: ${span}">
                      ${dayName}
                    </div>
                  `;
                })}
              </div>
            </div>
          </div>
          <div class="chart-legend">
            <span class="chart-legend-item">
              <span class="chart-legend-dot" style="background: var(--primary-color)"></span>
              Teraz
            </span>
            <span class="chart-legend-item">
              <span class="chart-legend-dot" style="background: var(--pstryk-green)"></span>
              Tania
            </span>
            <span class="chart-legend-item">
              <span class="chart-legend-dot" style="background: var(--pstryk-red)"></span>
              Droga
            </span>
            <span class="chart-legend-item">
              <span class="chart-legend-dot" style="background: var(--pstryk-blue)"></span>
              Normalna
            </span>
          </div>
        </ha-card>
      </div>
    `;
  }

  _renderPricingSection() {
    const prefix = "sensor.pstryk_energy_";
    const priceEntity = `${prefix}cena_energii_zakup_brutto`;

    const cheapestPrice = this._getAttr(priceEntity, "cheapest_upcoming_price");
    const cheapestStart = this._getAttr(priceEntity, "cheapest_upcoming_start");
    const cheapestEnd = this._getAttr(priceEntity, "cheapest_upcoming_end");
    const expensivePrice = this._getAttr(priceEntity, "most_expensive_upcoming_price");
    const expensiveStart = this._getAttr(priceEntity, "most_expensive_upcoming_start");
    const expensiveEnd = this._getAttr(priceEntity, "most_expensive_upcoming_end");

    return html`
      <div class="section-title">Nadchodzące ceny</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:arrow-down-bold-circle"></ha-icon>
            Najtańsza godzina
          </div>
          <div class="metric">
            <span class="metric-label">
              <ha-icon icon="mdi:clock-outline"></ha-icon>
              ${cheapestStart ? `${this._formatTime(cheapestStart)} - ${this._formatTime(cheapestEnd)}` : "---"}
            </span>
            <span class="metric-value">
              ${this._formatPrice(cheapestPrice)}
              ${cheapestPrice != null ? html`<span class="metric-unit">PLN/kWh</span>` : ""}
            </span>
          </div>
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:arrow-up-bold-circle"></ha-icon>
            Najdroższa godzina
          </div>
          <div class="metric">
            <span class="metric-label">
              <ha-icon icon="mdi:clock-outline"></ha-icon>
              ${expensiveStart ? `${this._formatTime(expensiveStart)} - ${this._formatTime(expensiveEnd)}` : "---"}
            </span>
            <span class="metric-value">
              ${this._formatPrice(expensivePrice)}
              ${expensivePrice != null ? html`<span class="metric-unit">PLN/kWh</span>` : ""}
            </span>
          </div>
        </ha-card>
      </div>
    `;
  }

  _hasTgeRdn() {
    const s = Object.keys(this.hass?.states || {});
    return s.some(e => e.startsWith("sensor.pstryk_energy_cena_rdn") || e.startsWith("sensor.tge_rdn_cena_rdn"));
  }

  _renderTgeRdnSection() {
    if (!this._hasTgeRdn()) return html``;

    // Encje mogą mieć prefix "tge_rdn_" (nowe instalacje) lub "pstryk_energy_" (stare)
    const st = this.hass?.states || {};
    const tid = (suffix) => {
      const a = `sensor.tge_rdn_${suffix}`;
      const b = `sensor.pstryk_energy_${suffix}`;
      return st[a] !== undefined ? a : b;
    };

    const currentEntity   = tid("cena_rdn_biezaca_godzina");
    const minTodayEntity  = tid("cena_rdn_najnizsza_dzis");
    const maxTodayEntity  = tid("cena_rdn_najwyzsza_dzis");
    const minTomorrowEntity = tid("cena_rdn_najnizsza_jutro");
    const maxTomorrowEntity = tid("cena_rdn_najwyzsza_jutro");

    const currentPrice = this._getState(currentEntity);
    const unit = this._getUnit(currentEntity) || "PLN/kWh";
    const currentHour = this._getAttr(currentEntity, "hour");
    const forecastToday = this._getAttr(currentEntity, "price_forecast_today") || [];
    const forecastTomorrow = this._getAttr(currentEntity, "price_forecast_tomorrow") || [];
    const tomorrowAvailable = this._getAttr(currentEntity, "tomorrow_available");

    const minTodayHour = this._getAttr(minTodayEntity, "hour");
    const maxTodayHour = this._getAttr(maxTodayEntity, "hour");
    const minTomorrowHour = this._getAttr(minTomorrowEntity, "hour");
    const maxTomorrowHour = this._getAttr(maxTomorrowEntity, "hour");

    return html`
      <div class="section-title">Ceny RDN Fixing I (TGE — brutto)</div>
      <div class="grid-full">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:chart-bar"></ha-icon>
            Ceny godzinowe RDN Fixing I
          </div>
          ${this._renderTgeRdnChart(forecastToday, forecastTomorrow, currentHour)}
        </ha-card>
        ${tomorrowAvailable && forecastTomorrow.length ? html`
          <ha-card>
            <div class="card-header">
              <ha-icon icon="mdi:chart-bar"></ha-icon>
              Ceny godzinowe RDN Jutro
            </div>
            ${this._renderTgeRdnChart(forecastTomorrow, [], -1)}
          </ha-card>
        ` : ""}
      </div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:currency-usd"></ha-icon>
            Aktualna cena RDN (brutto)
          </div>
          <div class="live-price-main" style="border-bottom: none; color: var(--primary-text-color);">
            <div>
              <span class="live-price-value" style="font-size: 28px;">${currentPrice !== null ? currentPrice : "---"}</span>
              <span class="live-price-unit" style="color: var(--secondary-text-color);">${unit}</span>
            </div>
            <div class="live-price-label" style="color: var(--secondary-text-color);">
              ${currentHour != null ? `Godzina ${String(currentHour).padStart(2, "0")}:00` : ""}
            </div>
          </div>
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:calendar-today"></ha-icon>
            Dziś
          </div>
          <div class="metric">
            <span class="metric-label">
              <ha-icon icon="mdi:arrow-down-bold"></ha-icon>
              Najniższa ${minTodayHour != null ? `(${String(minTodayHour).padStart(2, "0")}:00)` : ""}
            </span>
            <span class="metric-value">
              ${this._getState(minTodayEntity) !== null ? this._getState(minTodayEntity) : "---"}
              <span class="metric-unit">${unit}</span>
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">
              <ha-icon icon="mdi:arrow-up-bold"></ha-icon>
              Najwyższa ${maxTodayHour != null ? `(${String(maxTodayHour).padStart(2, "0")}:00)` : ""}
            </span>
            <span class="metric-value">
              ${this._getState(maxTodayEntity) !== null ? this._getState(maxTodayEntity) : "---"}
              <span class="metric-unit">${unit}</span>
            </span>
          </div>
        </ha-card>
        ${tomorrowAvailable ? html`
          <ha-card>
            <div class="card-header">
              <ha-icon icon="mdi:calendar-arrow-right"></ha-icon>
              Jutro
            </div>
            <div class="metric">
              <span class="metric-label">
                <ha-icon icon="mdi:arrow-down-bold"></ha-icon>
                Najniższa ${minTomorrowHour != null ? `(${String(minTomorrowHour).padStart(2, "0")}:00)` : ""}
              </span>
              <span class="metric-value">
                ${this._getState(minTomorrowEntity) !== null ? this._getState(minTomorrowEntity) : "---"}
                <span class="metric-unit">${unit}</span>
              </span>
            </div>
            <div class="metric">
              <span class="metric-label">
                <ha-icon icon="mdi:arrow-up-bold"></ha-icon>
                Najwyższa ${maxTomorrowHour != null ? `(${String(maxTomorrowHour).padStart(2, "0")}:00)` : ""}
              </span>
              <span class="metric-value">
                ${this._getState(maxTomorrowEntity) !== null ? this._getState(maxTomorrowEntity) : "---"}
                <span class="metric-unit">${unit}</span>
              </span>
            </div>
          </ha-card>
        ` : ""}
        ${this._renderTgeIndicatorsCard(currentPrice, this._getState(minTodayEntity), this._getState(maxTodayEntity), forecastToday, unit)}
      </div>
    `;
  }

  _renderTgeIndicatorsCard(currentPrice, minTodayStr, maxTodayStr, forecastToday, unit) {
    const cur = currentPrice !== null ? parseFloat(currentPrice) : NaN;
    const minToday = minTodayStr !== null ? parseFloat(minTodayStr) : NaN;
    const maxToday = maxTodayStr !== null ? parseFloat(maxTodayStr) : NaN;
    const prices = (forecastToday || []).map(f => f.price).filter(p => p != null);
    const avgVal = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : NaN;

    const round05 = (v) => isNaN(v) ? null : (Math.round(v / 0.05) * 0.05).toFixed(2);

    const cena0 = isNaN(cur) ? null : (cur <= 0 ? "1" : "0");
    const avgE23 = (isNaN(cur) || isNaN(avgVal)) ? null : (cur <= avgVal * 2 / 3 ? "1" : "0");
    const minR05 = round05(minToday);
    const maxR05 = round05(maxToday);
    const ltMin05 = (isNaN(cur) || isNaN(minToday)) ? null : (cur < minToday + 0.05 ? "1" : "0");
    const gtMax05 = (isNaN(cur) || isNaN(maxToday)) ? null : (cur > maxToday - 0.05 ? "1" : "0");
    const avgToday = isNaN(avgVal) ? null : avgVal.toFixed(4);
    const threshold = isNaN(avgVal) ? null : (avgVal * 2 / 3).toFixed(4);
    const minThreshold = isNaN(minToday) ? null : (minToday + 0.05).toFixed(4);
    const maxThreshold = isNaN(maxToday) ? null : (maxToday - 0.05).toFixed(4);

    const _badge = (val) => {
      if (val === null) return html`<span class="metric-unit">---</span>`;
      const active = String(val) === "1";
      return html`<span class="badge ${active ? "badge-cheap" : "badge-neutral"}" style="${active ? "" : "background:var(--secondary-text-color);opacity:0.6"}">${active ? "TAK" : "NIE"}</span>`;
    };

    return html`
      <ha-card>
        <div class="card-header">
          <ha-icon icon="mdi:gauge"></ha-icon>
          Wskaźniki TGE
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
            Cena ≤ 0 PLN/kWh
          </span>
          ${_badge(cena0)}
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:approximately-equal-box"></ha-icon>
            Cena ≤ 2/3 średniej dnia
          </span>
          ${_badge(avgE23)}
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:format-align-middle"></ha-icon>
            Średnia dnia
          </span>
          <span class="metric-value">
            ${avgToday != null ? Number(avgToday).toFixed(4) : "---"}
            <span class="metric-unit">${unit}</span>
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:ray-vertex"></ha-icon>
            Próg 2/3 średniej
          </span>
          <span class="metric-value">
            ${threshold != null ? Number(threshold).toFixed(4) : "---"}
            <span class="metric-unit">${unit}</span>
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:arrow-down-bold"></ha-icon>
            Min dziś (±0,05)
          </span>
          <span class="metric-value">
            ${minR05 !== null ? minR05 : "---"}
            <span class="metric-unit">${unit}</span>
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:arrow-up-bold"></ha-icon>
            Max dziś (±0,05)
          </span>
          <span class="metric-value">
            ${maxR05 !== null ? maxR05 : "---"}
            <span class="metric-unit">${unit}</span>
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:arrow-down-circle-outline"></ha-icon>
            Cena &lt; Min+0,05 ${minThreshold != null ? `(próg: ${Number(minThreshold).toFixed(4)})` : ""}
          </span>
          ${_badge(ltMin05)}
        </div>
        <div class="metric">
          <span class="metric-label">
            <ha-icon icon="mdi:arrow-up-circle-outline"></ha-icon>
            Cena &gt; Max−0,05 ${maxThreshold != null ? `(próg: ${Number(maxThreshold).toFixed(4)})` : ""}
          </span>
          ${_badge(gtMax05)}
        </div>
      </ha-card>
    `;
  }

  _renderTgeRdnChart(forecastToday, forecastTomorrow, currentHour) {
    const allEntries = [];
    const now = new Date();

    for (const e of forecastToday) {
      allEntries.push({
        hour: e.hour,
        price: e.price,
        day: "today",
        isCurrent: e.hour === currentHour && now.getDate() === new Date().getDate(),
      });
    }
    for (const e of forecastTomorrow) {
      allEntries.push({
        hour: e.hour,
        price: e.price,
        day: "tomorrow",
        isCurrent: false,
      });
    }

    if (!allEntries.length) {
      return html`<div class="empty-message">Brak danych RDN</div>`;
    }

    const prices = allEntries.map(e => e.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 0.01;
    const hasNegative = minPrice < 0;

    // For charts with negative values, calculate zero line position
    const zeroOffset = hasNegative ? Math.abs(minPrice) : 0;
    const totalRange = hasNegative ? maxPrice + zeroOffset : priceRange;

    const hasTomorrow = allEntries.some(e => e.day === "tomorrow");
    const labelInterval = allEntries.length > 30 ? 6 : 3;

    const priceLabelMax = maxPrice.toFixed(2);
    const priceLabelMin = minPrice.toFixed(2);
    const priceLabelMid = ((minPrice + maxPrice) / 2).toFixed(2);

    return html`
      <div class="chart-container">
        <div class="chart-price-labels">
          <span>${priceLabelMax}</span>
          <span>${priceLabelMid}</span>
          <span>${priceLabelMin}</span>
        </div>
        <div class="chart-body">
          <div class="chart-grid">
            <div class="chart-grid-line"></div>
            <div class="chart-grid-line chart-grid-line--dashed"></div>
            <div class="chart-grid-line chart-grid-line--dashed"></div>
          </div>
          <div class="chart-bars">
            ${allEntries.map((e, i) => {
              const pct = ((e.price - minPrice) / (totalRange || 0.01)) * 100;
              const barPct = Math.max(1.5, pct);
              let colorClass = "chart-bar--normal";
              if (e.isCurrent) colorClass = "chart-bar--current";
              else if (e.price === minPrice) colorClass = "chart-bar--cheap";
              else if (e.price === maxPrice) colorClass = "chart-bar--expensive";
              else if (e.price < 0) colorClass = "chart-bar--cheap";
              const isDaySep = i > 0 && e.day !== allEntries[i - 1].day;
              return html`
                <div class="chart-bar-col ${isDaySep ? 'chart-bar-col--sep' : ''}"
                     title="${String(e.hour).padStart(2, '0')}:00 — ${e.price.toFixed(4)} PLN/kWh">
                  <div class="chart-bar ${colorClass} ${e.isCurrent ? 'chart-bar--highlight' : ''}"
                       style="height: ${barPct}%"></div>
                </div>
              `;
            })}
          </div>
          <div class="chart-hour-labels">
            ${allEntries.map(e => html`
              <div class="chart-hour-label">
                ${e.hour % labelInterval === 0 ? String(e.hour).padStart(2, "0") : ""}
              </div>
            `)}
          </div>
          ${hasTomorrow ? html`
            <div class="chart-day-labels">
              <div class="chart-day-label" style="flex: ${allEntries.filter(e => e.day === 'today').length}">Dziś</div>
              <div class="chart-day-label" style="flex: ${allEntries.filter(e => e.day === 'tomorrow').length}">Jutro</div>
            </div>
          ` : ""}
        </div>
      </div>
      <div class="chart-legend">
        <span class="chart-legend-item">
          <span class="chart-legend-dot" style="background: var(--primary-color)"></span>
          Teraz
        </span>
        <span class="chart-legend-item">
          <span class="chart-legend-dot" style="background: var(--pstryk-green)"></span>
          Najtańsza
        </span>
        <span class="chart-legend-item">
          <span class="chart-legend-dot" style="background: var(--pstryk-red)"></span>
          Najdroższa
        </span>
        <span class="chart-legend-item">
          <span class="chart-legend-dot" style="background: var(--pstryk-blue)"></span>
          Normalna
        </span>
      </div>
    `;
  }

  _hasBleBox() {
    const prefix = "sensor.pstryk_meter_";
    return Object.keys(this.hass?.states || {}).some(e => e.startsWith(prefix));
  }

  _renderBleBoxSection() {
    if (!this._hasBleBox()) return html``;
    const p = "sensor.pstryk_meter_";
    return html`
      <div class="section-title">Licznik BleBox</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:flash"></ha-icon>
            Moc czynna
          </div>
          ${this._renderMetricIcon("mdi:sigma", "Suma", `${p}moc_czynna`)}
          ${this._renderMetricIcon("mdi:numeric-1-circle-outline", "L1", `${p}moc_czynna_l1`)}
          ${this._renderMetricIcon("mdi:numeric-2-circle-outline", "L2", `${p}moc_czynna_l2`)}
          ${this._renderMetricIcon("mdi:numeric-3-circle-outline", "L3", `${p}moc_czynna_l3`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:sine-wave"></ha-icon>
            Napięcie
          </div>
          ${this._renderMetricIcon("mdi:numeric-1-circle-outline", "L1", `${p}napiecie_l1`)}
          ${this._renderMetricIcon("mdi:numeric-2-circle-outline", "L2", `${p}napiecie_l2`)}
          ${this._renderMetricIcon("mdi:numeric-3-circle-outline", "L3", `${p}napiecie_l3`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:current-ac"></ha-icon>
            Prąd
          </div>
          ${this._renderMetricIcon("mdi:numeric-1-circle-outline", "L1", `${p}prad_l1`)}
          ${this._renderMetricIcon("mdi:numeric-2-circle-outline", "L2", `${p}prad_l2`)}
          ${this._renderMetricIcon("mdi:numeric-3-circle-outline", "L3", `${p}prad_l3`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:waveform"></ha-icon>
            Sieć
          </div>
          ${this._renderMetricIcon("mdi:sine-wave", "Częstotliwość", `${p}czestotliwosc_sieci`)}
          ${this._renderMetricIcon("mdi:transmission-tower-import", "Energia pobrana", `${p}energia_pobrana_licznik`)}
          ${this._renderMetricIcon("mdi:transmission-tower-export", "Energia oddana", `${p}energia_oddana_licznik`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:angle-acute"></ha-icon>
            tg φ (chwilowe)
          </div>
          ${this._renderMetricIcon("mdi:arrow-right-bold", "QI", `${p}tg_ph_qi_chwilowe`)}
          ${this._renderMetricIcon("mdi:arrow-left-bold", "QIV", `${p}tg_ph_qiv_chwilowe`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:angle-acute"></ha-icon>
            tg φ (miesiąc / rok)
          </div>
          ${this._renderMetricIcon("mdi:calendar-month", "QI miesiąc", `${p}tg_ph_qi_miesiac`)}
          ${this._renderMetricIcon("mdi:calendar-month", "QIV miesiąc", `${p}tg_ph_qiv_miesiac`)}
          ${this._renderMetricIcon("mdi:calendar", "QI rok", `${p}tg_ph_qi_rok`)}
          ${this._renderMetricIcon("mdi:calendar", "QIV rok", `${p}tg_ph_qiv_rok`)}
        </ha-card>
      </div>
    `;
  }

  _renderProsumerSection() {
    const prefix = "sensor.pstryk_energy_";
    const prosumerEntity = `${prefix}cena_sprzedazy_energii_brutto`;
    if (!this._entityExists(prosumerEntity)) {
      return html``;
    }
    const priceNet = this._getAttr(prosumerEntity, "price_net");
    return html`
      <div class="section-title">Prosument</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:solar-power"></ha-icon>
            Cena sprzedaży energii
          </div>
          ${this._renderMetricIcon("mdi:cash", "Cena brutto", prosumerEntity)}
          ${this._renderAttrMetric("mdi:cash-minus", "Cena netto", priceNet, "PLN/kWh")}
        </ha-card>
      </div>
    `;
  }

  render() {
    if (!this.hass) return html``;
    return html`
      <div class="header">
        <ha-icon icon="mdi:flash"></ha-icon>
        Pstryk Energy
        <div class="header-logos">
          <a class="header-logo" href="https://pstryk.pl" target="_blank" rel="noopener noreferrer">
            <img src="https://images.prismic.io/pstryk/aDiD4idWJ-7kSsSG_pstryk_logo.webp?auto=format,compress" alt="Pstryk">
          </a>
        </div>
      </div>
      ${this._renderLiveSection()}
      ${this._renderPriceChart()}
      ${this._renderPricingSection()}
      ${this._renderTgeRdnSection()}
      ${this._renderEnergySection()}
      ${this._renderCostSection()}
      ${this._renderBleBoxSection()}
      ${this._renderProsumerSection()}
    `;
  }
}

if (!customElements.get("pstryk-panel")) {
  customElements.define("pstryk-panel", PstrykPanel);
}
