/* We dynamically calculated the offsetWidth for the sticky columns. */
function calcStickyColumnsOffset() {
    const table = document.getElementById("lead-table");
    const rows = table.getElementsByTagName("tr");

    /* We iterate through each row. */
    for (let i = 0; i < rows.length; i++) {
        const row = rows.item(i);
        const stickyCollums = row.querySelectorAll(".sticky");
        let leftOffset = 0;

        /* We iterate through the columns which have the .sicky class. */
        for (let j = 0; j < stickyCollums.length; j++) {
            let col = stickyCollums.item(j);
            col.style.left = leftOffset + "px";
            leftOffset += col.offsetWidth;
        }
    }
}

calcStickyColumnsOffset();

window.addEventListener("resize", calcStickyColumnsOffset);