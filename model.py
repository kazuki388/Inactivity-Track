'''
Confined Timeout
Database Model definition

Copyright (C) 2024  __retr0.init__

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import sqlalchemy
from sqlalchemy import DateTime, BigInteger, String, JSON, Column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime
import pydantic

# class DBBase(DeclarativeBase):
class DBBase(AsyncAttrs, DeclarativeBase):
    pass

class UserTimeDB(DBBase):
    __tablename__ = "UserTimeDB"

    uid:        Mapped[int] = mapped_column(primary_key=True)
    user:       Mapped[int] = mapped_column(BigInteger, nullable=False)
    timestamp:  Mapped[float] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"UserTimeDB(user={self.user!r}, timestamp={self.timestamp!r})"

class StrippedRole(pydantic.BaseModel):
    id: int
    name: str

class StrippedRoles(pydantic.BaseModel):
    """
    To be used to validate StrippedUserDB roles
    {
        "roles": [
            {
                "id": 1234567890,
                "name": "Role1"
            },
            {
                "id": 1029384757,
                "name": "Role2"
            }
        ]
    }
    """
    roles: list[StrippedRole]

class StrippedUserDB(DBBase):
    __tablename__ = "StrippedUserDB"

    uid:        Mapped[int] = mapped_column(primary_key=True)
    user:       Mapped[int] = mapped_column(BigInteger, nullable=False)
    roles       = Column(JSON, nullable=False)

class ConfigRoles(pydantic.BaseModel):
    """
    Used for Config DB role json string: target, roles_given
    """
    roles: list[int]

class ConfigDB(DBBase):
    """
    Configuration database. Arbitrary value, no migration needed.

    Current configs (Name | Type | Description):
    - action | bool | Whether the module should take action or just take statistics
    - period | int | The period (in hours) to think as inactive user
    - target | str(str or json) | The target role to execute actions. Direct "all" means everyone. JSON string limits to specific roles only: {"roles": [1234, 2345]}. {"roles": []} means no one will be taken actions.
    - roles_given | str(json) | The role(s) given to the executed members. {"roles": [1234, 2345]} assigns the roles with the IDs. {"roles": []} means no role will be assigned.
    """
    __tablename__ = "ConfigDB"

    uid:        Mapped[int] = mapped_column(primary_key=True)
    name:       Mapped[str] = mapped_column(nullable=False)
    value:      Mapped[str]
