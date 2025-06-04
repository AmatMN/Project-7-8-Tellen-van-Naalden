function poll() {
    const data = [
        { "type": "c1", "num": 5 }, { "type": "c2", "num": 2 }, { "type": "c3", "num": 7 }, { "type": "c4", "num": 2 }, { "type": "h2", "num": 3 }, { "type": "g5", "num": 7 }, { "type": "c9", "num": 1 }, { "type": "d2", "num": 2 }, { "type": "f5", "num": 5 }
    ];
    let items = "";
    data.forEach((type) => {
        items += `
        <tr>
            <td>${type.type}</td>
            <td>${type.num}</td>
        </tr>`;
    });
    document.getElementById("Needle-data").innerHTML = items;
}
