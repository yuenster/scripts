$Properties = @( 'Title', 'Department', 'Manager' )
$groupresult = @()

    [string[]]$arrayFromFile = Get-Content -Path 'C:\sslvpn-active.txt'
    foreach($group in $arrayFromFile){
        #Write-Output $group
        #Write-Output "----------------------------"
        $searchb = "CN="+"$group"+",OU=SSLVPN,OU=UserGroupsRAS,DC=li,DC=lumentuminc,DC=net"
    
        $groupresult = Get-ADGroupMember $searchb |
        Get-ADUser -Properties $Properties |
        Where-Object{ $_.Enabled } |

        Select-Object @{Name = "Group"; Expression = { $group }}, 
            Name, Title, Department,
            @{Name = "ManagerName"; Expression = { (Get-ADUser $_.Manager).Name }}, 
            @{Name = "ManagerMail"; Expression = { (Get-ADUser $_.Manager -Properties mail).Mail }} 
        $result += $groupresult
          
    }

$result | Export-Csv -Path 'C:\manager-info.csv' -NoTypeInformation