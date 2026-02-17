/**
 * Runs callback when DOM is ready (analog of jQuery $(document).ready()).
 * @param {() => void} fn
 * @returns {void}
 */
export const onDocumentReady = (fn) => {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fn);
    } else {
        fn();
    }
}