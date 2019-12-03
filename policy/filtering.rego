package filtering

## access list for proejcts that don't have a DAC
entitlements = {"alice":["tertiary"],
                "bob":  ["primary"]}

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
  input.method = "GET"
  input.token.payload.researcher = true
  input.path = ["individuals", iid]
  some i
  data.consents[x].id == entitlements[input.user][i]
}