package static

consents = {"P001":["profyle_member"],
            "P002":["profyle_member"],
            "P003":["profyle_member"],
            "P004":["tf4cn_member"],
            "P005":["tf4cn_member"],
            "P006":["tf4cn_member"]}

import input

id_token = {"payload": payload} { io.jwt.decode(input.id_token, [_, payload, _]) }
claims_tokens = [ payload | io.jwt.decode(input.claims_tokens[i], [_, payload, _])]

allowed_claims_set = { j | claims_tokens[i][j] }

default allow = false

# Allow users get data they're authorized for if they are researchers
allow {
  input.method = "GET"
  id_token.payload.researcher = true
  input.path = ["individuals", iid]
  consents[iid][i] == allowed_claims_set[j]
}
