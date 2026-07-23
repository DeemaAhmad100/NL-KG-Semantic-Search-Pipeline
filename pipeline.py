"""End-to-end NL-question pipeline against the recipe KG.

Wires `mapper.detect_shape → mapper.extract_slots → mapper.compile_to_cypher
→ driver.session().run(cypher, **params)` into one function. Raises
`UnsupportedQueryError` (fail-loud) when the question is off-template.
"""

from mapper import (
    detect_shape,
    extract_slots,
    compile_to_cypher,
    UnsupportedQueryError,
)


def answer(driver, question: str) -> list[dict]:
    """Answer one NL question by routing through the deterministic mapper.

    Returns a list of result rows (each row a dict whose keys are the
    Cypher RETURN aliases). Raises UnsupportedQueryError when
    detect_shape returns None — surface that to the caller; do not
    swallow it into an empty result list.
    """
    # 1. Detect the shape
    shape = detect_shape(question)
    if shape is None:
        raise UnsupportedQueryError(question)
    
    # 2. Extract slots for the detected shape
    slots = extract_slots(question, shape)
    
    # 3. Compile to Cypher and params
    cypher, params = compile_to_cypher(shape, slots)
    
    # 4. Execute the query and collect results
    with driver.session() as session:
        result = session.run(cypher, **params)
        return [row.data() for row in result]

