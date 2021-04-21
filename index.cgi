#!/bin/bash
#
# @(#) Build all the directories
#
MYHOST=$(hostname)
DE_DATE=$(date "+%m/%d/%Y %H:%M:%S")

cat <<EOF1
Content-type: text/html

<html>
	<head>
		<title>
			GPIB Athena
		</title>
		<META http-equiv="refresh" content="60">
		<style>
			table {
				margin-left: auto;
				margin-right: auto;
				width:90%;
				border-collapse: collapse;
				border:none;
			}
			table.roundedCorners {
				margin-left: auto;
				margin-right: auto;
				width:90%;
				border-collapse: collapse;
				border:none;
			}
			table.roundedCorners tr:nth-child(even) {
				color: Red;
				background-color: #f2f2f2;
			}
			table.roundedCorners tr:nth-child(even) a{
				color: Blue;
				background-color: #f2f2f2;
			}
			table.roundedCorners tr:nth-child(odd) {
				color: White;
				background-color: #0033cc;
			}
			table.roundedCorners tr:nth-child(odd) a{
				color: White;
				background-color: #0033cc;
			}
			table.roundedCorners tr:hover {background-color: #ffcccc;color: Blue;}
			table.roundedCorners tr:hover a{background-color: #ffcccc;color: Blue;}
		    .footer {
				position: absolute !important;
				left: 0;
				bottom: 0;
				width: 100%;
				background-color: #539FD0;
				color: red;
				text-align: center;
			}
		</style>
	</head>
	<body style="background-color:#e6e6e6">
			<table style="border-collapse:collapse;border:none;border-width: 1px 0;"> 
				<tr>
					<td style="width:10%;background-color:#e6e6e6;">
						<div style="font-family:courier;font-weight:bold;font-size:16pt;text-align:center;">
							&nbsp;
						</div>
					</td>
					<td style="width:80%;background-color:Black">
						<div style="font-family:courier;font-weight:bold;font-size:18pt;text-align:center;color:Red">
							[ ${MYHOST} ] Instrument Scans<BR>
						</div>
						<div style="font-family:courier;font-weight:bold;font-size:8pt;text-align:center;color:White">
							${DE_DATE}
						</div>
					</td>
					<td style="width:10%;background-color:#e6e6e6;">
						&nbsp;
					</td>
				</tr>
			</table>
			<BR>
			<table class="roundedCorners">
EOF1
#
if [[ -z $GPIB_SCANDIR ]]
then
	GPIB_SCANDIR="/var/www/html/GPIB/scans"
fi
#
TEXT_COLOR="Black"
#
ls -t $GPIB_SCANDIR | while read line
do
	BNAME=$(basename $line)
	echo -e "<tr>"
	echo -e "<td style=\"width:10%;\">"
		echo -e "&nbsp;"
	echo -e "</td>"
	echo -e "<td style=\"width:40%;border:solid;border-top:none;border-left:none;border-bottom:none;border-right:none;text-align:Center;\">"
		MAIN_CAP=$(cat ${GPIB_SCANDIR}/${BNAME}/gpib_description_MAIN_CAPTURE_DESCRIPTION.html)
		echo -e "<a href=\"scans/${BNAME}/index.shtml\" style=\"font-family:Courier;font-weight:Bold;font-size:16pt;text-decoration:none;\">&nbsp;${MAIN_CAP}</a>"
	echo -e "</td>"
	#
	echo -e "<td style=\"width:1%;background-color:#e6e6e6\">"
		echo -e "&nbsp;"
	echo -e "</td>"
	#
	read line
	if [[ -z $line ]]
	then
		echo -e "<td style=\"width:39%;White;border-right:1px 0;\">"
			echo -e "&nbsp;"
		echo -e "</td>"
	else
		BNAME=$(basename $line)
		echo -e "<td style=\"width:39%;text-align:Center;\">"
			MAIN_CAP=$(cat ${GPIB_SCANDIR}/${BNAME}/gpib_description_MAIN_CAPTURE_DESCRIPTION.html)
			echo -e "<a href=\"scans/${BNAME}/index.shtml\" style=\"font-family:Courier;font-weight:Bold;font-size:16pt;text-decoration: none;\">&nbsp;${MAIN_CAP}</a>"
		echo -e "</td>"
	fi
	echo -e "<td style=\"width:10%;\">"
		echo -e "&nbsp;"
	echo -e "</td>"
	echo -e "</tr>"
done
cat <<-EOF2
			</table>
		<!-- Footer -->
		<div class="footer">
			<table style="width:100%;border:none;border-collapse:collapse;">
				<tr>
					<td style="width:10%">
						&nbsp;
					</td>
					<td style="width:80%">
						<div style="color:black;background:white;">
							<table style="width:100%;border:1px solid black;border-collapse:collapse;color:black;">
								<tr>
									<td style="text-align:center;width:10%">&nbsp;</td>
									<td style="text-align:center;width:70%;border: none;">
										<a href="https://github.com/linuxaos/GPIB-Code" style="color:${TEXT_COLOR};font-family:Courier;font-weight:Bold;font-size:16pt;text-decoration: none;">Github GPIB Code</a>
									</td>
									<td style="text-align:center;width:20%">
										&nbsp;
									</td>
								</tr>
							</table>
						</div>
					</td>
					<td style="width:10%">
						&nbsp;
					</td>
				</tr>
			</table>
		</div>
		<script>
			var dt = new Date();
			document.getElementById("datetime").innerHTML = dt.toLocaleString('en-GB')
		</script>
	</body>
</html>
EOF2
