package static

consents = {"P001":["primary", "secondaryA"],
            "P002":["primary", "secondaryA"],
            "P003":["primary", "secondaryA"],
            "P004":["primary", "secondaryB"],
            "P005":["primary", "secondaryB"],
            "P006":["primary", "secondaryB"]}

import input

token = {"payload": payload} { io.jwt.decode(input.token, [_, payload, _]) }

# input = {
#   "path": ["individuals", "P001"],
#   "user": "alice",
#   "method": "GET"
#    token.payload.entitlements == ["primary", "secondaryA"]
#    token.payload.researcher == "True"
# }

default allow = false

# Allow users get data they're authorized for if they are researchers
allow {
  input.method = "GET"
  token.payload.researcher = true
  input.path = ["individuals", iid]
  consents[iid][i] == token.payload.entitlements[j]
}
