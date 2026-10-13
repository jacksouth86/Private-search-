// ==UserScript==
// @name         Bazaraki Private Seller Filter
// @namespace    https://grok.x.ai
// @version      2.0
// @description  Automatically hide business/agency listings on Bazaraki real estate pages and highlight private sellers
// @author       Grok
// @match        https://www.bazaraki.com/*
// @match        https://m.bazaraki.com/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    const BUSINESS_INDICATORS = [
        'ltd', 'limited', 'llc', 'real estate', 'estates', 'realty', 'properties',
        'property', 're/max', 'remax', 'century 21', 'century21', 'sotheby',
        'agency', 'agent', 'developers', 'development', 'holdings', 'group',
        'verified business', 'business account', 'company', 'office', 'cy ltd',
        'cyprus', 's.r.l', 'gmbh', 'inc'
    ];

    function looksLikeBusiness(text) {
        if (!text) return false;
        const lower = text.toLowerCase();
        return BUSINESS_INDICATORS.some(word => lower.includes(word));
    }

    function filterListings() {
        // Try multiple possible selectors for listing cards
        const selectors = [
            '.advert-list-item',
            '.list-item',
            '.search-item',
            '.item',
            '[class*="advert"]',
            '[class*="listing"]',
            'div[data-id]',
            '.card'
        ];

        let processed = 0;
        let hidden = 0;

        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el.dataset.filtered) return;
                el.dataset.filtered = '1';
                processed++;

                // Look for seller name in common places
                const sellerText = (
                    el.querySelector('.seller-name, .user-name, .author, .company-name, a[href*="/c/"]')?.textContent ||
                    el.textContent
                );

                if (looksLikeBusiness(sellerText)) {
                    el.style.display = 'none';
                    hidden++;
                } else {
                    el.style.outline = '2px solid #34a853';
                    el.style.borderRadius = '6px';
                }
            });
        });

        // Floating counter
        let badge = document.getElementById('private-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'private-badge';
            badge.style.cssText = `
                position:fixed;bottom:16px;right:16px;z-index:999999;
                background:#34a853;color:white;padding:10px 14px;
                border-radius:20px;font:14px system-ui;box-shadow:0 4px 12px rgba(0,0,0,.2);
            `;
            document.body.appendChild(badge);
        }
        badge.textContent = `Private filter active • ${hidden} business hidden`;
    }

    // Run repeatedly because Bazaraki loads results dynamically
    filterListings();
    setInterval(filterListings, 2000);

    // Also watch for DOM changes
    const observer = new MutationObserver(() => setTimeout(filterListings, 500));
    observer.observe(document.body, { childList: true, subtree: true });

    console.log('[Private Filter] Running on Bazaraki');
})();
