"""Systems called from tick slots.

Information is generated first, then the first hop scales it by q. Each later information_forward hop multiplies the received payload by fidelity. When fidelity is 1, those hops copy the payload unchanged. Representative decision produces an action intent only.
"""
