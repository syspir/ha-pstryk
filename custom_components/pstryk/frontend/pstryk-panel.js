// Twoje-Miasto Sp. z o.o. / Marcin Koźliński
// Ostatnia modyfikacja: 2026-03-28

const LitElement =
  customElements.get("hui-view") ?
    Object.getPrototypeOf(customElements.get("hui-view")) :
    Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));

const html = LitElement.prototype.html;

// W nowszych HA css nie jest na prototypie LitElement — tworzymy kompatybilną implementację
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
        color: var(--secondary-text-color);
        font-size: 14px;
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
      .live-card .metric-value {
        color: var(--text-primary-color);
        font-size: 16px;
      }
      .live-card .metric {
        border-bottom-color: rgba(255,255,255,0.15);
      }
      .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        color: white;
      }
      .badge-cheap {
        background: var(--pstryk-green);
      }
      .badge-expensive {
        background: var(--pstryk-red);
      }
      .badge-neutral {
        background: var(--secondary-text-color);
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
      .live-card .price-time {
        color: rgba(255,255,255,0.7);
      }
      @media (max-width: 600px) {
        :host { padding: 8px; }
        .grid { grid-template-columns: 1fr; }
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

  _formatValue(entityId) {
    const val = this._getState(entityId);
    if (val === null) return "---";
    const unit = this._getUnit(entityId);
    return `${val}${unit ? ` ${unit}` : ""}`;
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

  _renderMetric(label, entityId) {
    const val = this._getState(entityId);
    const unit = this._getUnit(entityId);
    return html`
      <div class="metric">
        <span class="metric-label">${label}</span>
        <span class="metric-value">
          ${val !== null ? val : "---"}
          ${val !== null && unit ? html`<span class="metric-unit">${unit}</span>` : ""}
        </span>
      </div>
    `;
  }

  _renderLiveSection() {
    const prefix = "sensor.pstryk_energy_";
    return html`
      <div class="section-title">Bieżąca godzina</div>
      <div class="grid-full">
        <ha-card class="live-card">
          <div class="card-header">
            <ha-icon icon="mdi:pulse"></ha-icon>
            Dane na żywo
          </div>
          ${this._renderMetric("Energia pobrana", `${prefix}energy_import_current_hour`)}
          ${this._renderMetric("Energia oddana", `${prefix}energy_export_current_hour`)}
          ${this._renderMetric("Koszt", `${prefix}cost_current_hour`)}
          ${this._renderMetric("Cena TGE", `${prefix}unified_price_current_hour`)}
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
          ${this._renderMetric("Pobrana", `${prefix}energy_import_today`)}
          ${this._renderMetric("Oddana", `${prefix}energy_export_today`)}
          ${this._renderMetric("Bilans", `${prefix}energy_balance_today`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:calendar-month"></ha-icon>
            Miesiąc
          </div>
          ${this._renderMetric("Pobrana", `${prefix}energy_import_month`)}
          ${this._renderMetric("Oddana", `${prefix}energy_export_month`)}
          ${this._renderMetric("Bilans", `${prefix}energy_balance_month`)}
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
          ${this._renderMetric("Koszt energii", `${prefix}total_cost_today`)}
          ${this._renderMetric("Wartość sprzedanej", `${prefix}energy_sold_value_today`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:cash-multiple"></ha-icon>
            Miesiąc
          </div>
          ${this._renderMetric("Koszt energii", `${prefix}total_cost_month`)}
          ${this._renderMetric("Wartość sprzedanej", `${prefix}energy_sold_value_month`)}
        </ha-card>
      </div>
    `;
  }

  _renderPricingSection() {
    const prefix = "sensor.pstryk_energy_";
    const isCheap = this._getState(`${prefix}is_cheap_now`);
    const isExpensive = this._getState(`${prefix}is_expensive_now`);

    const cheapestStart = this._getAttr(`${prefix}cheapest_upcoming_price`, "start");
    const cheapestEnd = this._getAttr(`${prefix}cheapest_upcoming_price`, "end");
    const expensiveStart = this._getAttr(`${prefix}most_expensive_upcoming_price`, "start");
    const expensiveEnd = this._getAttr(`${prefix}most_expensive_upcoming_price`, "end");

    let badge = html``;
    if (isCheap === "True") {
      badge = html`<span class="badge badge-cheap">Tania energia</span>`;
    } else if (isExpensive === "True") {
      badge = html`<span class="badge badge-expensive">Droga energia</span>`;
    } else if (isCheap !== null) {
      badge = html`<span class="badge badge-neutral">Normalna cena</span>`;
    }

    return html`
      <div class="section-title">Ceny TGE (giełda energii)</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:currency-usd"></ha-icon>
            Aktualne ceny
            ${badge}
          </div>
          ${this._renderMetric("Cena brutto", `${prefix}current_price_gross`)}
          ${this._renderMetric("Cena netto", `${prefix}current_price_net`)}
          ${this._renderMetric("Pełna cena (z dystrybucją)", `${prefix}current_full_price`)}
          ${this._renderMetric("Średnia brutto", `${prefix}avg_price_gross`)}
          ${this._renderMetric("Średnia netto", `${prefix}avg_price_net`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:chart-timeline-variant"></ha-icon>
            Nadchodzące ceny
          </div>
          <div class="metric">
            <div>
              <div class="metric-label">Najtańsza</div>
              ${cheapestStart ? html`<div class="price-time">${this._formatTime(cheapestStart)} - ${this._formatTime(cheapestEnd)}</div>` : ""}
            </div>
            <span class="metric-value">${this._formatValue(`${prefix}cheapest_upcoming_price`)}</span>
          </div>
          <div class="metric">
            <div>
              <div class="metric-label">Najdroższa</div>
              ${expensiveStart ? html`<div class="price-time">${this._formatTime(expensiveStart)} - ${this._formatTime(expensiveEnd)}</div>` : ""}
            </div>
            <span class="metric-value">${this._formatValue(`${prefix}most_expensive_upcoming_price`)}</span>
          </div>
        </ha-card>
      </div>
    `;
  }

  _renderProsumerSection() {
    const prefix = "sensor.pstryk_energy_";
    if (!this._entityExists(`${prefix}prosumer_price_gross`)) {
      return html``;
    }
    return html`
      <div class="section-title">Prosument</div>
      <div class="grid">
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:solar-power"></ha-icon>
            Ceny prosumenckie
          </div>
          ${this._renderMetric("Cena brutto", `${prefix}prosumer_price_gross`)}
          ${this._renderMetric("Cena netto", `${prefix}prosumer_price_net`)}
          ${this._renderMetric("Średnia brutto", `${prefix}prosumer_avg_price_gross`)}
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
      </div>
      ${this._renderLiveSection()}
      ${this._renderEnergySection()}
      ${this._renderCostSection()}
      ${this._renderPricingSection()}
      ${this._renderProsumerSection()}
    `;
  }
}

customElements.define("pstryk-panel", PstrykPanel);
