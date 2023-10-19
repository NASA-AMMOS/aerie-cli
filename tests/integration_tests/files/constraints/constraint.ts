export default (): Constraint => {
    return Discrete.Resource('/flag').equal('B')
  }
  