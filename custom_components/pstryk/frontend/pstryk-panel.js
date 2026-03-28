// Twoje-Miasto Sp. z o.o. / Marcin Koźliński
// Ostatnia modyfikacja: 2026-03-28

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
  // Czekaj aż HA załaduje elementy Lovelace
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
          ${this._renderMetric("Energia pobrana", `${prefix}energia_pobrana_biezaca_godzina`)}
          ${this._renderMetric("Energia oddana", `${prefix}energia_oddana_biezaca_godzina`)}
          ${this._renderMetric("Koszt", `${prefix}koszt_biezaca_godzina`)}
          ${this._renderMetric("Cena TGE", `${prefix}cena_tge_biezaca_godzina_z_metryki`)}
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
          ${this._renderMetric("Pobrana", `${prefix}energia_pobrana_dzis`)}
          ${this._renderMetric("Oddana", `${prefix}energia_oddana_dzis`)}
          ${this._renderMetric("Bilans", `${prefix}bilans_energii_dzis`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:calendar-month"></ha-icon>
            Miesiąc
          </div>
          ${this._renderMetric("Pobrana", `${prefix}energia_pobrana_w_miesiacu`)}
          ${this._renderMetric("Oddana", `${prefix}energia_oddana_w_miesiacu`)}
          ${this._renderMetric("Bilans", `${prefix}bilans_energii_w_miesiacu`)}
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
          ${this._renderMetric("Koszt energii", `${prefix}koszt_energii_dzis`)}
          ${this._renderMetric("Wartość sprzedanej", `${prefix}wartosc_sprzedanej_energii_dzis`)}
        </ha-card>
        <ha-card>
          <div class="card-header">
            <ha-icon icon="mdi:cash-multiple"></ha-icon>
            Miesiąc
          </div>
          ${this._renderMetric("Koszt energii", `${prefix}koszt_energii_w_miesiacu`)}
          ${this._renderMetric("Wartość sprzedanej", `${prefix}wartosc_sprzedanej_energii_w_miesiacu`)}
        </ha-card>
      </div>
    `;
  }

  _renderPricingSection() {
    const prefix = "sensor.pstryk_energy_";
    const isCheap = this._getState(`${prefix}tania_energia_teraz`);
    const isExpensive = this._getState(`${prefix}droga_energia_teraz`);

    const cheapestStart = this._getAttr(`${prefix}najtansza_nadchodzaca_cena`, "start");
    const cheapestEnd = this._getAttr(`${prefix}najtansza_nadchodzaca_cena`, "end");
    const expensiveStart = this._getAttr(`${prefix}najdrozsza_nadchodzaca_cena`, "start");
    const expensiveEnd = this._getAttr(`${prefix}najdrozsza_nadchodzaca_cena`, "end");

    let badge = html``;
    if (isCheap === "True" || isCheap === "1") {
      badge = html`<span class="badge badge-cheap">Tania energia</span>`;
    } else if (isExpensive === "True" || isExpensive === "1") {
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
          ${this._renderMetric("Cena brutto", `${prefix}aktualna_cena_energii_brutto`)}
          ${this._renderMetric("Cena netto", `${prefix}aktualna_cena_energii_netto`)}
          ${this._renderMetric("Pełna cena (z dystrybucją)", `${prefix}pelna_cena_energii_z_dystrybucja`)}
          ${this._renderMetric("Średnia brutto", `${prefix}srednia_cena_energii_brutto`)}
          ${this._renderMetric("Średnia netto", `${prefix}srednia_cena_energii_netto`)}
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
            <span class="metric-value">${this._formatValue(`${prefix}najtansza_nadchodzaca_cena`)}</span>
          </div>
          <div class="metric">
            <div>
              <div class="metric-label">Najdroższa</div>
              ${expensiveStart ? html`<div class="price-time">${this._formatTime(expensiveStart)} - ${this._formatTime(expensiveEnd)}</div>` : ""}
            </div>
            <span class="metric-value">${this._formatValue(`${prefix}najdrozsza_nadchodzaca_cena`)}</span>
          </div>
        </ha-card>
      </div>
    `;
  }

  _renderProsumerSection() {
    const prefix = "sensor.pstryk_energy_";
    if (!this._entityExists(`${prefix}cena_prosumencka_brutto`)) {
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
          ${this._renderMetric("Cena brutto", `${prefix}cena_prosumencka_brutto`)}
          ${this._renderMetric("Cena netto", `${prefix}cena_prosumencka_netto`)}
          ${this._renderMetric("Średnia brutto", `${prefix}srednia_cena_prosumencka_brutto`)}
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
            <img src="https://pstryk.pl/img/logo.svg" alt="Pstryk">
          </a>
          <a class="header-logo" href="https://www.twoje-miasto.pl" target="_blank" rel="noopener noreferrer">
            <img src="https://im.twoje-miasto.pl/theme/1/images/logo.png" alt="Twoje-Miasto">
          </a>
        </div>
      </div>
      ${this._renderLiveSection()}
      ${this._renderEnergySection()}
      ${this._renderCostSection()}
      ${this._renderPricingSection()}
      ${this._renderProsumerSection()}
    `;
  }
}

if (!customElements.get("pstryk-panel")) {
  customElements.define("pstryk-panel", PstrykPanel);
}
