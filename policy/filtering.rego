package filtering

## access list for proejcts that don't have a DAC
access_list = {"alice":["tf4cn_member"],
               "bob":  ["tf4cn_member"]}

# authorization is denied if the identity token is expired
# or if signature fails validation
allow = false {
  [valid, header, payload] := io.jwt.decode_verify(input.user, {"secret": "secret"})
  valid == false
}

idtoken := {"payload": payload} { io.jwt.decode(input.user, [_, payload, _]) }
subject := idtoken.payload.sub

# authorize a single item
allow = true {
  input.method = "GET"
  input.path = ["individuals", iid]
  some x
  row_allowed[x]
  data.individuals[x].id = iid
}

# authorize items from a list
allow = true {
  input.method = "GET"
  input.path = ["individuals"]
  some x
  row_allowed[x]
}

# Item is allowed if the input consent (e.g. from a DAC) matches the data consent...
row_allowed[x] {
  some i
  data.individuals[x].id = data.consents[x].id 
  data.consents[x].consent = true
  data.consents[x].project = input.entitlements[i]
}

# Item is also allowed if the data consent matches an entitlement in access list above
row_allowed[x] {
  some j
  data.individuals[x].id = data.consents[x].id 
  data.consents[x].consent = true
  data.consents[x].project = access_list[subject][j]
}