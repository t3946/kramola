import u, {Umbrella} from 'umbrellajs';
import socketIOService from "../../../../frontend/src/services/SocketioService";

class Parsing {
    page: Umbrella
    watchKeys: Set<string>
    shouldReloadOnDone: boolean

    constructor() {
        this.page = u('.parsingPage')
        this.watchKeys = new Set([
            "parser:status:InagentsXlsxParser",
            "parser:status:ParserFedsFM",
        ])
        this.shouldReloadOnDone = this._hasRunningStatus()

        if (this.page.length > 0) {
            this._subscribeSocketEvents()
        }
    }

    _hasRunningStatus(): boolean {
        const statusNodes: Element[] = Array.from(
            document.querySelectorAll(".parsingPage [data-parsing-status]")
        )

        return statusNodes.some((node: Element): boolean => {
            const statusText: string = (node.textContent || "").trim()

            return statusText === "В работе"
        })
    }

    _subscribeSocketEvents(): void {
        socketIOService.on("parsing_status_changed", (payload: { key?: string; state?: string } | null) => {
            if (!payload || !payload.key || !payload.state) {
                return
            }

            if (!this.watchKeys.has(payload.key)) {
                return
            }

            if (payload.state === "running") {
                this.shouldReloadOnDone = true
                return
            }

            if (payload.state === "done" && this.shouldReloadOnDone) {
                window.location.reload()
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