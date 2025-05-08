local logins = {}
local file = io.open("user_logins.txt", "r")
for line in file:lines() do
    logins[#logins + 1] = line
end
file:close()

request = function()
    local id = math.random(1, #logins)
    local path = "/users/" .. logins[id]
    local header = {["Authorization"] = "Bearer ..."} -- place token here 
    return wrk.format("GET", path)