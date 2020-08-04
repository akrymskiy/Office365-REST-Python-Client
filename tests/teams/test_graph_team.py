import uuid
from time import sleep

from tests.graph_case import GraphTestCase

from office365.graph.directory.group import Group
from office365.graph.directory.groupProfile import GroupProfile
from office365.runtime.client_request_exception import ClientRequestException


class TestGraphTeam(GraphTestCase):
    """Tests for teams"""

    target_group = None  # type: Group

    @staticmethod
    def ensure_group(client, properties):
        """

        :type client: GraphClient
        :type properties: GroupProfile
        :return: Group
        """
        target_group = client.groups.add(properties)

        def _ensure_group_provisioned(resp):
            for retry in range(1, 5):
                try:
                    existing_group = client.groups[target_group.id]
                    client.load(existing_group)
                    client.execute_query()
                    if existing_group:
                        break
                except ClientRequestException:
                    sleep(5)

        client.after_execute(_ensure_group_provisioned)
        return target_group

    @classmethod
    def setUpClass(cls):
        super(TestGraphTeam, cls).setUpClass()
        grp_name = "Group_" + uuid.uuid4().hex
        properties = GroupProfile(grp_name)
        properties.securityEnabled = False
        properties.mailEnabled = True
        properties.groupTypes = ["Unified"]
        # cls.target_group = cls.client.groups.add(properties)
        cls.target_group = cls.ensure_group(cls.client, properties)
        cls.client.execute_query()

    def test2_ensure_team(self):
        teams = self.client.me.joinedTeams.filter("id eq '{0}'".format(self.__class__.target_group.id))
        self.client.load(teams)
        self.client.execute_query()
        self.assertIsNotNone(teams.resource_path)

        if len(teams) == 0:
            new_team = self.__class__.target_group.add_team()
            self.client.execute_query()
            self.assertIsNotNone(new_team)
        else:
            self.assertEqual(len(teams), 1)

    def test3_get_team(self):
        group_id = self.__class__.target_group.id
        existing_team = self.client.teams[group_id]
        self.client.load(existing_team)
        self.client.execute_query()
        self.assertIsNotNone(existing_team.resource_url)
        self.assertIsNotNone(existing_team.messagingSettings)

        if existing_team.properties["isArchived"]:
            existing_team.unarchive()
            self.client.load(existing_team)
            self.client.execute_query()
            self.assertFalse(existing_team.properties["isArchived"])

    def test4_update_team(self):
        group_id = self.__class__.target_group.properties['id']
        team_to_update = self.client.teams[group_id]
        team_to_update.funSettings.allowGiphy = False
        team_to_update.update()
        self.client.execute_query()

    def test5_archive_team(self):
        group_id = self.__class__.target_group.id
        team_to_archive = self.client.teams[group_id]
        team_to_archive.archive()
        self.client.execute_query()

    def test6_delete_group_with_team(self):
        grp_to_delete = self.__class__.target_group
        grp_to_delete.delete_object(True)
        self.client.execute_query()
