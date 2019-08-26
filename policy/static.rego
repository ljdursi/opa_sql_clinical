package static

consents = {"P001":["primary", "secondaryA"],
            "P002":["primary", "secondaryA"],
            "P003":["primary", "secondaryA"],
            "P004":["primary", "secondaryB"],
            "P005":["primary", "secondaryB"],
            "P006":["primary", "secondaryB"]}

import input

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
  input.token.payload.researcher = true
  input.path = ["individuals", iid]
  consents[iid][i] == input.token.payload.entitlements[j]
}
