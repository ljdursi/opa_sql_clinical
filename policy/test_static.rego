package static

test_valid_allowed {
    allow with input as { "path": ["individuals", "P001"],
                          "user": "alice",
                          "method": "GET",
                          "token": {"payload":{"researcher":true, "entitlements": ["primary", "secondaryA"]}} }
}

test_wrong_entitlement_disallowed {
    not allow with input as { "path": ["individuals", "P001"],
                              "user": "alice",
                              "method": "GET",
                              "token": {"payload":{"researcher":true, "entitlements": ["secondaryB"]}} }
}

test_notaresearcher_disallowed {
    not allow with input as { "path": ["individuals", "P001"],
                              "user": "bob",
                              "method": "GET",
                              "token": {"payload":{"researcher":false, "entitlements": ["primary", "secondaryA"]}} }
}

test_noentitlements_disallowed {
    not allow with input as { "path": ["individuals", "P001"],
                              "user": "frank",
                              "method": "GET",
                              "token": {"payload":{"researcher":true, "entitlements": []}} }
}
