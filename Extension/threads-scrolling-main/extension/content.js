const processedElements = new WeakSet();

function sendToPython(element) {
    if (processedElements.has(element)) return;
    
    const text = element.innerText;
    if (!text || text.trim().length === 0) return;

    processedElements.add(element);
    const rect = element.getBoundingClientRect();
    
    const payload = {
        text: text.trim(),
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height
    };

    try {
        chrome.runtime.sendMessage({
            action: "sendToPython",
            data: payload
        }, (response) => {
            if (response && response.is_target === true) {
                element.style.backgroundColor = "#000000";
                element.style.color = "#000000";
                element.style.borderRadius = "4px";
            }
        });
    } catch (error) {}
}

function scanThreads() {
    document.querySelectorAll('div[data-virtualized="false"]').forEach(wrapper => {
        if (!wrapper.closest('[data-pagelet^="threads_post_page_"]')) return;
        
        const autoSpans = [...wrapper.querySelectorAll('span[dir="auto"]')];
        
        autoSpans.forEach((span, i) => {
            // Text bình luận luôn ở index 2, 8, 14... (mỗi comment chiếm ~6 span)
            if (i % 6 === 2) {
                sendToPython(span);
            }
        });
    });
}

setInterval(scanThreads, 2000);