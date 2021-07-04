def addItUp(x, y) { x + y }

def globals = [:]

globals << [hook : [
  onStartUp: { ctx ->
    ctx.logger.info("Loading 'Knowledge Graph' graph data.")
    graph.io(graphml()).readGraph('data/g.graphml')
  }
] as LifeCycleHook]

globals << [g : graph.traversal()]
