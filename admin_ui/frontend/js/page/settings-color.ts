/**
 * Search settings color page: color swatch pickers with palette
 */
import iro from "@jaames/iro";

const STANDARD_COLORS = [
  "#ff0031", // #ff0031
  "#ffae00", // #ffae00
  "#ffdd00", // #ffdd00
  "#13ff00", // #13ff00
  "#00dfff", // #00dfff
  "#4eadfb", // #4eadfb
  "#cf75ff", // #cf75ff
];

function hexToHue(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  if (max !== min) {
    const d = max - min;
    if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
    else if (max === g) h = ((b - r) / d + 2) / 6;
    else h = ((r - g) / d + 4) / 6;
  }
  return h * 360;
}

function sortBySpectrum(hexArr: string[]): string[] {
  return hexArr.slice().sort((a, b) => hexToHue(a) - hexToHue(b));
}

/**
 * One color row: swatch button + popover with palette and iro picker
 */
class ColorSwatchRow {
  private readonly wrap: HTMLElement;
  private readonly input: HTMLInputElement;
  private readonly swatchBtn: HTMLButtonElement;
  private readonly popover: HTMLElement;
  private readonly paletteEl: HTMLElement;
  private readonly pickerEl: HTMLElement;
  private picker: ReturnType<typeof iro.ColorPicker> | null = null;

  constructor(wrap: HTMLElement) {
    this.wrap = wrap;
    const input = wrap.querySelector('input[type="hidden"]');
    const swatchBtn = wrap.querySelector(".color-swatch");
    const popover = wrap.querySelector(".color-swatch-popover");
    const paletteEl = wrap.querySelector(".color-palette");
    const pickerEl = wrap.querySelector(".color-swatch-picker");
    if (
      !input ||
      !swatchBtn ||
      !popover ||
      !paletteEl ||
      !pickerEl ||
      !(input instanceof HTMLInputElement) ||
      !(swatchBtn instanceof HTMLButtonElement)
    ) {
      throw new Error("ColorSwatchRow: required elements not found");
    }
    this.input = input;
    this.swatchBtn = swatchBtn;
    this.popover = popover as HTMLElement;
    this.paletteEl = paletteEl as HTMLElement;
    this.pickerEl = pickerEl as HTMLElement;
    this.init();
  }

  private init(): void {
    const initialColor = this.wrap.getAttribute("data-initial-color") ?? "#6b7280";
    this.picker = new iro.ColorPicker(this.pickerEl, {
      width: 160,
      color: initialColor,
      layout: [
        { component: iro.ui.Wheel },
        { component: iro.ui.Slider, options: { sliderType: "value" as const } },
      ],
    });
    this.renderPalette();
    this.picker.on("color:change", (color: { hexString: string }) => {
      this.updateFromPicker(color.hexString);
    });
    this.updateFromPicker(initialColor);
    this.swatchBtn.addEventListener("click", (e) => this.onSwatchClick(e));
  }

  private updateFromPicker(hex: string): void {
    this.input.value = hex;
    this.swatchBtn.style.backgroundColor = hex;
    const previewId = this.wrap.getAttribute("data-preview-for");
    if (previewId) {
      const el = document.getElementById(previewId);
      if (el) (el as HTMLElement).style.backgroundColor = hex;
    }
  }

  private renderPalette(): void {
    this.paletteEl.style.display = "grid";
    this.paletteEl.style.gridTemplateColumns = "repeat(8, 32px)";
    this.paletteEl.style.gap = "10px";
    this.paletteEl.style.marginBottom = "12px";
    STANDARD_COLORS.forEach((hex) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "rounded-md border border-gray-300 cursor-pointer hover:ring-2 hover:ring-gray-400";
      btn.style.width = "32px";
      btn.style.height = "32px";
      btn.style.minWidth = "32px";
      btn.style.minHeight = "32px";
      btn.style.backgroundColor = hex;
      btn.setAttribute("aria-label", "Цвет " + hex);
      btn.addEventListener("click", () => {
        if (this.picker) {
          this.picker.color.hexString = hex;
          this.updateFromPicker(hex);
        }
      });
      this.paletteEl.appendChild(btn);
    });
  }

  private onSwatchClick(e: Event): void {
    e.preventDefault();
    const isHidden = this.popover.classList.contains("hidden");
    document.querySelectorAll(".color-swatch-popover").forEach((p) => {
      p.classList.add("hidden");
    });
    if (isHidden) this.popover.classList.remove("hidden");
  }
}

/**
 * Settings color page: inits all color swatch rows on the search settings view
 */
function init(): void {
  if (!document.querySelector(".color-swatch-wrap")) return;
  const wraps = document.querySelectorAll(".color-swatch-wrap");
  wraps.forEach((el) => {
    if (el instanceof HTMLElement && !(el as HTMLElement & { _colorRow?: ColorSwatchRow })._colorRow) {
      (el as HTMLElement & { _colorRow?: ColorSwatchRow })._colorRow = new ColorSwatchRow(el);
    }
  });
  document.addEventListener("click", (e: Event) => {
    if ((e.target as Element).closest(".color-swatch-wrap")) return;
    document.querySelectorAll(".color-swatch-popover").forEach((p) => {
      p.classList.add("hidden");
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
