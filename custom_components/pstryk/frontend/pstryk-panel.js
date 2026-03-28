// Marcin Koźliński
// Ostatnia modyfikacja: 2026-03-29

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
      .chart-container {
        position: relative;
        width: 100%;
        padding: 8px 0;
      }
      .chart-svg {
        width: 100%;
        height: 200px;
        display: block;
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
      .chart-day-label {
        font-size: 11px;
        font-weight: 500;
        fill: var(--secondary-text-color);
        text-anchor: middle;
      }
      @media (max-width: 600px) {
        :host { padding: 8px; }
        .grid { grid-template-columns: 1fr; }
        .live-grid { grid-template-columns: 1fr; }
        .chart-svg { height: 160px; }
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
      return html``;
    }

    // Group frames by day
    const now = new Date();
    const todayStr = now.toLocaleDateString("pl-PL");
    const frames = forecast
      .filter(f => f.start && (f.full_price != null || f.price_gross != null))
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

    if (!frames.length) return html``;

    const prices = frames.map(f => f.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 0.01;

    // Chart dimensions
    const chartW = 100; // percentage based
    const chartH = 160;
    const padTop = 20;
    const padBottom = 30;
    const padLeft = 0;
    const padRight = 0;
    const barAreaH = chartH - padTop - padBottom;

    const barCount = frames.length;
    const barGap = 1;
    const barW = Math.max(1, (chartW - padLeft - padRight) / barCount - barGap);

    // Find day boundaries for labels
    const days = [];
    let lastDateStr = "";
    frames.forEach((f, i) => {
      if (f.dateStr !== lastDateStr) {
        days.push({ index: i, dateStr: f.dateStr, date: f.date });
        lastDateStr = f.dateStr;
      }
    });

    const dayNames = ["Niedz.", "Pon.", "Wt.", "Śr.", "Czw.", "Pt.", "Sob."];

    const bars = frames.map((f, i) => {
      const x = padLeft + i * (barW + barGap);
      const normalizedH = ((f.price - minPrice) / priceRange) * barAreaH;
      const barH = Math.max(2, normalizedH);
      const y = padTop + barAreaH - barH;

      let color;
      if (f.isCurrent) {
        color = "var(--primary-color)";
      } else if (f.isCheap === true || f.isCheap === "True") {
        color = "var(--pstryk-green)";
      } else if (f.isExpensive === true || f.isExpensive === "True") {
        color = "var(--pstryk-red)";
      } else {
        color = "var(--pstryk-blue)";
      }

      return { x, y, barH, barW, color, frame: f };
    });

    // Hour labels (every 3h or 6h depending on count)
    const labelInterval = barCount > 30 ? 6 : 3;
    const hourLabels = frames
      .map((f, i) => ({ hour: f.hour, x: padLeft + i * (barW + barGap) + barW / 2, index: i, dateStr: f.dateStr }))
      .filter(l => l.hour % labelInterval === 0);

    // Price labels
    const priceLabelMin = minPrice.toFixed(2);
    const priceLabelMax = maxPrice.toFixed(2);
    const priceLabelMid = ((minPrice + maxPrice) / 2).toFixed(2);

    // SVG viewBox based on percentage width
    const svgW = padLeft + barCount * (barW + barGap) + padRight;

    return html`
      <div class="section-title">Prognoza cen</div>
      <div class="grid-full">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:chart-bar"></ha-icon>
            Ceny godzinowe (zakup brutto)
          </div>
          <div class="chart-container">
            <svg class="chart-svg" viewBox="0 0 ${svgW} ${chartH}" preserveAspectRatio="none">
              <!-- grid lines -->
              <line x1="${padLeft}" y1="${padTop}" x2="${svgW - padRight}" y2="${padTop}"
                    stroke="var(--divider-color)" stroke-width="0.3" stroke-dasharray="2,2"/>
              <line x1="${padLeft}" y1="${padTop + barAreaH / 2}" x2="${svgW - padRight}" y2="${padTop + barAreaH / 2}"
                    stroke="var(--divider-color)" stroke-width="0.3" stroke-dasharray="2,2"/>
              <line x1="${padLeft}" y1="${padTop + barAreaH}" x2="${svgW - padRight}" y2="${padTop + barAreaH}"
                    stroke="var(--divider-color)" stroke-width="0.3"/>

              <!-- price labels -->
              <text x="${svgW - 1}" y="${padTop + 3}" text-anchor="end"
                    font-size="3.5" fill="var(--secondary-text-color)">${priceLabelMax}</text>
              <text x="${svgW - 1}" y="${padTop + barAreaH / 2 + 1.5}" text-anchor="end"
                    font-size="3.5" fill="var(--secondary-text-color)">${priceLabelMid}</text>
              <text x="${svgW - 1}" y="${padTop + barAreaH - 1}" text-anchor="end"
                    font-size="3.5" fill="var(--secondary-text-color)">${priceLabelMin}</text>

              <!-- bars -->
              ${bars.map(b => html`
                <rect x="${b.x}" y="${b.y}" width="${b.barW}" height="${b.barH}"
                      fill="${b.color}" rx="0.5"
                      opacity="${b.frame.isCurrent ? 1 : 0.8}">
                  <title>${b.frame.hour}:00 — ${b.frame.price.toFixed(4)} PLN/kWh</title>
                </rect>
                ${b.frame.isCurrent ? html`
                  <rect x="${b.x - 0.3}" y="${b.y - 1}" width="${b.barW + 0.6}" height="${b.barH + 2}"
                        fill="none" stroke="var(--primary-text-color)" stroke-width="0.5" rx="0.8"/>
                ` : ""}
              `)}

              <!-- day separator lines -->
              ${days.slice(1).map(d => {
                const x = padLeft + d.index * (barW + barGap) - barGap / 2;
                return html`
                  <line x1="${x}" y1="${padTop - 5}" x2="${x}" y2="${padTop + barAreaH + 2}"
                        stroke="var(--secondary-text-color)" stroke-width="0.4" stroke-dasharray="2,1"/>
                `;
              })}

              <!-- hour labels -->
              ${hourLabels.map(l => html`
                <text x="${l.x}" y="${padTop + barAreaH + 10}"
                      text-anchor="middle" font-size="3.5" fill="var(--secondary-text-color)">
                  ${String(l.hour).padStart(2, "0")}
                </text>
              `)}

              <!-- day labels -->
              ${days.map((d, di) => {
                const nextIdx = di + 1 < days.length ? days[di + 1].index : frames.length;
                const midIdx = d.index + (nextIdx - d.index) / 2;
                const x = padLeft + midIdx * (barW + barGap);
                const dayName = d.date.toDateString() === now.toDateString()
                  ? "Dziś"
                  : d.date.toDateString() === new Date(now.getTime() + 86400000).toDateString()
                    ? "Jutro"
                    : dayNames[d.date.getDay()];
                return html`
                  <text x="${x}" y="${padTop + barAreaH + 20}"
                        text-anchor="middle" font-size="4" font-weight="500"
                        fill="var(--secondary-text-color)">
                    ${dayName}
                  </text>
                `;
              })}
            </svg>
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
      ${this._renderEnergySection()}
      ${this._renderCostSection()}
      ${this._renderProsumerSection()}
    `;
  }
}

if (!customElements.get("pstryk-panel")) {
  customElements.define("pstryk-panel", PstrykPanel);
}
