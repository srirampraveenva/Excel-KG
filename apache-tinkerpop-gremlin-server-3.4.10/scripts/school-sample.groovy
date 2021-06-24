def globals = [:]

globals << [hook : [
  onStartUp: { ctx ->
    ctx.logger.info("Loading 'school' graph data.")
    graph.io(graphml()).readGraph('data/g.graphml')
  }
] as LifeCycleHook]

globals << [g : graph.traversal()]
