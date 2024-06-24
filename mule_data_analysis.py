import pandas as pd
import json
import http.server
import socketserver
import webbrowser

def generate_and_serve():
    # Load your dataset from Excel (replace 'layers.xlsx' with your actual Excel filename)
    df = pd.read_excel('layers.xlsx')

    # Assuming 'accountid', 'crimeid', 'amount', and 'bankname' are column names in your Excel sheet
    accountids = df['accountid'].unique().tolist()
    crimeids = df['crimeid'].unique().tolist()

    nodes = [{'id': acc, 'group': 'accountid', 'bankname': df[df['accountid'] == acc]['bankname'].iloc[0]} for acc in accountids]
    nodes.extend({'id': crime, 'group': 'crimeid'} for crime in crimeids)

    links = [{'source': row['accountid'], 'target': row['crimeid'], 'amount': row['amount']} for _, row in df.iterrows()]

    graph = {'nodes': nodes, 'links': links}

    # Calculate node degrees and total amount
    node_degree = {}
    total_amount = 0
    for link in links:
        node_degree[link['source']] = node_degree.get(link['source'], 0) + 1
        node_degree[link['target']] = node_degree.get(link['target'], 0) + 1
        total_amount += link['amount']

    for node in nodes:
        node['degree'] = node_degree.get(node['id'], 0)

    # Save the data to a JSON file
    with open('cyber_frauds_graph.json', 'w') as f:
        json.dump(graph, f)

    # HTML content for serving the D3.js visualization (index.html)
    index_html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cyber Frauds Link Analysis</title>
        <script src="https://d3js.org/d3.v6.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
            body {{
                display: flex;
                flex-direction: column;
                margin: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-image: url('https://www.transparenttextures.com/patterns/old-map.png'); /* Set background image */
                color: #fff; /* Set text color to white for better visibility */
                height: 100vh;
            }}
            #header {{
                position: absolute;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent background */
                padding: 5px 10px; /* Reduced padding */
                border-radius: 10px;
                font-size: 24px; /* Reduced font size */
                font-family: 'Pacifico', cursive;
                color: #fff;
                text-shadow: 2px 2px #000;
                z-index: 1000;
            }}
            #sidebar {{
                width: 300px;
                height: 100vh;
                overflow-y: auto;
                border-right: 1px solid #ddd;
                padding: 10px;
                box-sizing: border-box;
                background-color: #333; /* Set sidebar background color to dark grey */
                color: #fff; /* Set sidebar text color to white */
            }}
            #viz {{
                flex: 1;
                height: 100vh;
                overflow: hidden;
                background-color: rgba(0, 0, 0, 0.8); /* Set visualization area background color */
                position: relative;
            }}
            svg {{
                width: 100%;
                height: 100%;
            }}
            .node {{
                stroke: #fff;
                stroke-width: 1.5px;
                cursor: pointer;
                transition: stroke 0.3s ease; /* Remove scaling effect */
            }}
            .node:hover {{
                stroke: yellow; /* Change stroke color on hover for better visibility */
            }}
            .link {{
                stroke: #fff; /* Set link color to white */
                stroke-opacity: 0.6;
                transition: all 0.3s ease;
            }}
            text {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12px;
                fill: #fff; /* Set text color to white */
            }}
            .highlighted {{
                stroke: red;
                stroke-width: 2px;
            }}
            .highlighted-link {{
                stroke: red;
                stroke-width: 2px;
            }}
            .total-amount {{
                position: absolute;
                bottom: 10px;
                right: 10px;
                font-size: 16px;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 5px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            }}
            .btn {{
                position: absolute;
                top: 50px;
                right: 10px;
                padding: 10px 20px;
                font-size: 16px;
                color: #fff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                margin-right: 10px;
                font-family: 'Pacifico', cursive; /* Match font with the header */
            }}
            .btn:hover {{
                background-color: #0056b3;
            }}
            .tooltip {{
                position: absolute;
                text-align: center;
                width: auto;
                height: auto;
                padding: 8px;
                font: 12px sans-serif;
                background: lightsteelblue;
                border: 0;
                border-radius: 8px;
                pointer-events: none;
            }}
            .legend {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                font-size: 14px;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 5px;
                color: white;
            }}
            .legend div {{
                margin-bottom: 5px;
            }}
            .highlight {{
                stroke: red;
                stroke-width: 3px;
            }}
        </style>
    </head>
    <body>
        <div id="header">Catch 'em All</div>
        <div id="viz">
            <button class="btn" onclick="resetView()">Reset View</button>
            <svg>
                <defs>
                    <pattern id="accountPattern" width="100%" height="100%" patternContentUnits="objectBoundingBox">
                        <image href="https://img.icons8.com/color/48/000000/user.png" preserveAspectRatio="xMidYMid slice" width="1" height="1"></image>
                    </pattern>
                    <pattern id="crimePattern" width="100%" height="100%" patternContentUnits="objectBoundingBox">
                        <image href="https://img.icons8.com/color/48/000000/computer.png" preserveAspectRatio="xMidYMid slice" width="1" height="1"></image>
                    </pattern>
                </defs>
                <g class="everything"></g>
            </svg>
            <div class="total-amount">Total Amount: {total_amount}</div>
            <div class="legend">
                <div><span style="color: #ADD8E6;"><img src="https://img.icons8.com/color/48/000000/user.png" width="20" height="20"></span> Account ID</div>
                <div><span style="color: #FFA500;"><img src="https://img.icons8.com/color/48/000000/computer.png" width="20" height="20"></span> Crime ID</div>
            </div>
        </div>
        <script>
            let simulation, svg, everything, zoom, width, height, graph;

            function resetView() {{
                svg.transition().duration(750).call(
                    zoom.transform,
                    d3.zoomIdentity.translate(width / 2, height / 2).scale(0.8) // Adjusted scale
                );
            }}

            // Load the data
            d3.json('cyber_frauds_graph.json').then(function(g) {{
                graph = g;
                width = document.getElementById('viz').clientWidth;
                height = document.getElementById('viz').clientHeight;

                svg = d3.select("svg");
                everything = svg.select(".everything");

                // Set up zoom behavior
                zoom = d3.zoom()
                    .scaleExtent([0.1, 10])
                    .on("zoom", zoomed);

                svg.call(zoom);

                // Initial zoom transform
                svg.call(zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2).scale(0.8)); // Adjusted initial scale

                const sizeScale = d3.scaleLinear()
                    .domain([0, d3.max(graph.nodes, function(d) {{ return d.degree; }})])
                    .range([5, 20]); // Adjust node size based on degree

                simulation = d3.forceSimulation(graph.nodes)
                    .force("link", d3.forceLink(graph.links).id(function(d) {{ return d.id; }}).distance(100).strength(1))
                    .force("charge", d3.forceManyBody().strength(-100))
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("collision", d3.forceCollide().radius(function(d) {{ return sizeScale(d.degree) + 10; }}))
                    .on("tick", ticked);

                const tooltip = d3.select("body").append("div")
                    .attr("class", "tooltip")
                    .style("opacity", 0);

                const link = everything.append("g")
                    .attr("class", "links")
                    .selectAll("line")
                    .data(graph.links)
                    .enter().append("line")
                    .attr("class", "link")
                    .attr("stroke-dasharray", "5,5") // Add dashed lines for links
                    .attr("marker-end", "url(#arrow)");

                const node = everything.append("g")
                    .attr("class", "nodes")
                    .selectAll("rect")
                    .data(graph.nodes)
                    .enter().append("rect")
                    .attr("class", "node")
                    .attr("width", function(d) {{ return sizeScale(d.degree) * 2; }}) // Adjust size based on degree
                    .attr("height", function(d) {{ return sizeScale(d.degree) * 2; }}) // Adjust size based on degree
                    .attr("fill", function(d) {{ return d.group === 'accountid' ? 'url(#accountPattern)' : 'url(#crimePattern)'; }})
                    .on("click", nodeClicked)
                    .on("mouseover", function(event, d) {{
                        const connectedLinks = graph.links.filter(link => link.source.id === d.id || link.target.id === d.id);
                        const connectedNodes = connectedLinks.map(link => link.source.id === d.id ? link.target.id : link.source.id);
                        const connectedAmounts = connectedLinks.map(link => link.amount);

                        tooltip.transition().duration(200).style("opacity", .9);
                        tooltip.html(`
                            <strong>ID:</strong> ` + d.id + `<br/>
                            <strong>Connected Nodes:</strong> ` + connectedNodes.join(", ") + `<br/>
                            <strong>Amounts:</strong> ` + connectedAmounts.join(", ") + `
                        `)
                        .style("left", (event.pageX + 5) + "px")
                        .style("top", (event.pageY - 28) + "px");
                    }})
                    .on("mouseout", function() {{
                        tooltip.transition().duration(500).style("opacity", 0);
                    }})
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                const text = everything.append("g")
                    .attr("class", "texts")
                    .selectAll("text")
                    .data(graph.nodes)
                    .enter().append("text")
                    .attr("dx", 12)
                    .attr("dy", ".35em")
                    .text(function(d) {{ return d.id; }});

                function ticked() {{
                    link
                        .attr("x1", function(d) {{ return d.source.x; }})
                        .attr("y1", function(d) {{ return d.source.y; }})
                        .attr("x2", function(d) {{ return d.target.x; }})
                        .attr("y2", function(d) {{ return d.target.y; }});

                    node
                        .attr("x", function(d) {{ return d.x - sizeScale(d.degree); }})
                        .attr("y", function(d) {{ return d.y - sizeScale(d.degree); }});

                    text
                        .attr("x", function(d) {{ return d.x; }})
                        .attr("y", function(d) {{ return d.y; }});
                }}

                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }}

                function dragged(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }}

                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}

                function zoomed(event) {{
                    everything.attr("transform", event.transform);
                }}

                function nodeClicked(event, d) {{
                    // Debugging output
                    console.log('Node clicked: ' + d.id);

                    // Perform BFS to find all connected nodes and links
                    const queue = [d.id];
                    const visitedNodes = new Set();
                    const visitedLinks = new Set();
                    visitedNodes.add(d.id);

                    while (queue.length > 0) {{
                        const currentNode = queue.shift();
                        graph.links.forEach(link => {{
                            if (link.source.id === currentNode && !visitedNodes.has(link.target.id)) {{
                                queue.push(link.target.id);
                                visitedNodes.add(link.target.id);
                                visitedLinks.add(link);
                            }} else if (link.target.id === currentNode && !visitedNodes.has(link.source.id)) {{
                                queue.push(link.source.id);
                                visitedNodes.add(link.source.id);
                                visitedLinks.add(link);
                            }}
                        }});
                    }}

                    // Highlight the nodes and links
                    svg.selectAll(".link")
                        .classed("highlighted-link", function(link) {{
                            return visitedLinks.has(link);
                        }})
                        .attr("stroke", function(link) {{
                            return visitedLinks.has(link) ? "red" : "#fff";
                        }})
                        .attr("stroke-opacity", function(link) {{
                            return visitedLinks.has(link) ? 1 : 0.6;
                        }});

                    svg.selectAll(".node")
                        .classed("highlighted", function(node) {{
                            return visitedNodes.has(node.id);
                        }})
                        .attr("stroke", function(node) {{
                            return visitedNodes.has(node.id) ? "red" : "#fff";
                        }})
                        .attr("stroke-width", function(node) {{
                            return visitedNodes.has(node.id) ? 3 : 1.5;
                        }});

                    // Open details window
                    const subgraphWindow = window.open("details.html", "_blank", "width=800,height=600");

                    // Filter and prepare data for the subgraph
                    const relatedLinks = graph.links.filter(function(link) {{ return visitedLinks.has(link); }});
                    const relatedNodes = relatedLinks.map(function(link) {{
                        const sourceNode = graph.nodes.find(function(node) {{ return node.id === link.source.id; }});
                        const targetNode = graph.nodes.find(function(node) {{ return node.id === link.target.id; }});

                        return {{
                            crimeid: link.target.id,
                            accountid: link.source.id,
                            bankname: sourceNode.bankname,
                            amount: link.amount
                        }};
                    }});

                    subgraphWindow.onload = function () {{
                        subgraphWindow.renderSubgraph(d.id, relatedNodes);
                    }};
                }}
            }});

            function zoomed(event) {{
                everything.attr("transform", event.transform);
            }}
        </script>
    </body>
    </html>
    """

    # Save HTML content to a file
    with open('index.html', 'w') as f_index:
        f_index.write(index_html_content)

    # Serve the files using Python's built-in HTTP server
    PORT = 8004  # Changed port number to avoid conflicts

    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        webbrowser.open_new_tab(f'http://localhost:{PORT}/index.html')
        httpd.serve_forever()

if __name__ == "__main__":
    generate_and_serve()
