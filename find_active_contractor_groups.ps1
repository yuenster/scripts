$SSLVPN = Get-ADGroup -filter * -SearchBase 'OU=SSLVPN,OU=UserGroupsRAS,DC=li,DC=companyinc,DC=net'
$result = @()
foreach($group in $SSLVPN) {
    foreach ($user in Get-ADGroupMember $group) {
        if(Get-ADUser -identity $user -Properties Enabled | Where-Object {$_.Enabled -eq $True})
        {
            $result += $group | select name 
            break           
        }
     
     }
}
write-output $result
# write-output $result | Export-Csv -Path c:\sslvpn.csv -NoTypeInformation   