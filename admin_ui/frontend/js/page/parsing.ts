import u, {Umbrella} from 'umbrellajs';
import socketIOService from "../../../../frontend/src/services/SocketioService";

type TParsingStatus = "Выполенено" | "В работе" | "Не проводилось";

interface IParsingSocketPayload {
    key?: string;
    state?: string;
    status?: TParsingStatus;
    last_parse?: string;
    can_run?: boolean;
}

interface IRunResponse {
    success?: boolean;
    payload?: IParsingSocketPayload;
}

interface IParsingRowUi {
    row: HTMLElement;
    dateNode: HTMLElement | null;
    statusNode: HTMLElement | null;
    runButton: HTMLButtonElement | null;
}

class Parsing {
    page: Umbrella
    watchKeys: Set<string>
    rows: Map<string, IParsingRowUi>

    constructor() {
        this.page = u('.parsingPage')
        this.watchKeys = new Set([
            "parser:status:InagentsXlsxParser",
            "parser:status:ParserFedsFM",
        ])
        this.rows = this._collectRows()

        if (this.page.length > 0) {
            this._bindRunForms()
            this._subscribeSocketEvents()
        }
    }

    _collectRows(): Map<string, IParsingRowUi> {
        const result: Map<string, IParsingRowUi> = new Map<string, IParsingRowUi>()
        const rowNodes: Element[] = Array.from(document.querySelectorAll(".parsingPage [data-parsing-key]"))

        rowNodes.forEach((node: Element): void => {
            if (!(node instanceof HTMLElement)) {
                return
            }

            const key: string = (node.dataset.parsingKey || "").trim()
            if (!key) {
                return
            }

            const dateNode: HTMLElement | null = node.querySelector("[data-parsing-date]")
            const statusNode: HTMLElement | null = node.querySelector("[data-parsing-status]")
            const runButtonNode: Element | null = node.querySelector("[data-parsing-run-button]")
            const runButton: HTMLButtonElement | null = runButtonNode instanceof HTMLButtonElement ? runButtonNode : null

            result.set(key, {
                row: node,
                dateNode,
                statusNode,
                runButton,
            })
        })

        return result
    }

    _statusClass(status: TParsingStatus): string {
        if (status === "Выполенено") {
            return "bg-green-100 text-green-800"
        }

        if (status === "В работе") {
            return "bg-yellow-100 text-yellow-800"
        }

        return "bg-red-100 text-red-800"
    }

    _applyButtonState(button: HTMLButtonElement, canRun: boolean): void {
        button.disabled = !canRun

        button.classList.remove("btn__primary", "btn__disabled")

        if (canRun) {
            button.classList.add("btn__primary")
            return
        }

        button.classList.add("btn__disabled")
    }

    _applyRealtimeUpdate(payload: IParsingSocketPayload): void {
        const key: string = (payload.key || "").trim()
        if (!key || !this.watchKeys.has(key)) {
            return
        }

        const rowUi: IParsingRowUi | undefined = this.rows.get(key)
        if (!rowUi) {
            return
        }

        if (typeof payload.last_parse === "string" && rowUi.dateNode) {
            rowUi.dateNode.textContent = payload.last_parse
        }

        if (typeof payload.status === "string" && rowUi.statusNode) {
            const status: TParsingStatus = payload.status as TParsingStatus
            rowUi.statusNode.textContent = status
            rowUi.statusNode.classList.remove("bg-green-100", "text-green-800", "bg-yellow-100", "text-yellow-800", "bg-red-100", "text-red-800")
            rowUi.statusNode.classList.add(...this._statusClass(status).split(" "))
        }

        if (typeof payload.can_run === "boolean" && rowUi.runButton) {
            this._applyButtonState(rowUi.runButton, payload.can_run)
        }
    }

    _subscribeSocketEvents(): void {
        socketIOService.on("parsing_status_changed", (payload: IParsingSocketPayload | null) => {
            this._applyRealtimeUpdate(payload || {})
        })
    }

    _bindRunForms(): void {
        const forms: Element[] = Array.from(document.querySelectorAll(".parsingPage [data-parsing-run-form]"))

        forms.forEach((node: Element): void => {
            if (!(node instanceof HTMLFormElement)) {
                return
            }

            node.addEventListener("submit", (event: Event) => {
                event.preventDefault()

                const rowNode: Element | null = node.closest("[data-parsing-key]")
                const key: string = rowNode instanceof HTMLElement ? (rowNode.dataset.parsingKey || "").trim() : ""
                if (!key) {
                    return
                }

                this._runUpdate(node, key)
            })
        })
    }

    _runUpdate(form: HTMLFormElement, key: string): void {
        const rowUi: IParsingRowUi | undefined = this.rows.get(key)
        if (rowUi?.runButton?.disabled) {
            return
        }

        if (rowUi?.runButton) {
            this._applyButtonState(rowUi.runButton, false)
        }

        if (rowUi?.statusNode) {
            rowUi.statusNode.textContent = "В работе"
            rowUi.statusNode.classList.remove("bg-green-100", "text-green-800", "bg-yellow-100", "text-yellow-800", "bg-red-100", "text-red-800")
            rowUi.statusNode.classList.add("bg-yellow-100", "text-yellow-800")
        }

        fetch(form.action, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(async (response: Response): Promise<IRunResponse> => {
                if (!response.ok) {
                    throw new Error("Request failed")
                }

                return response.json() as Promise<IRunResponse>
            })
            .then((data: IRunResponse) => {
                if (data?.payload) {
                    this._applyRealtimeUpdate(data.payload)
                    return
                }

                if (rowUi?.runButton) {
                    this._applyButtonState(rowUi.runButton, true)
                }
            })
            .catch(() => {
                if (rowUi?.runButton) {
                    this._applyButtonState(rowUi.runButton, true)
                }
            })
    }
}

function init(): void {
    if (u(".parsingPage").length === 0) {
        return
    }

    new Parsing()
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init)
} else {
    init()
}