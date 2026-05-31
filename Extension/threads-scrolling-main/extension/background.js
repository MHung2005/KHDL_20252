// Lắng nghe tin nhắn từ content.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "sendToPython") {
        
        // Thực hiện fetch từ Background (không bị Facebook chặn)
        fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(request.data)
        })
        .then(response => response.json())
        .then(data => {
            sendResponse(data);
        })
        .catch(error => sendResponse({error: true}));
        
        // Trả về true để báo là đã nhận tin
        return true; 
    }
});